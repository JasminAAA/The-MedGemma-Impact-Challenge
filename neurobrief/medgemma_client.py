import re
import json

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class MedGemmaClient:
    def __init__(self, use_real_model=True):
        """
        use_real_model=False → heuristic demo mode
        use_real_model=True  → integrate real MedGemma API
        """
        self.use_real_model = use_real_model
        self.tokenizer = None
        self.model = None

        if use_real_model:
            print("Loading MedGemma 1.5...")
            self.tokenizer = AutoTokenizer.from_pretrained("google/medgemma-1.5-4b-it")

            # Add padding token if missing (prevents tokenization errors)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                "google/medgemma-1.5-4b-it",
                torch_dtype=torch.float16,
                device_map="auto",
            )

            # Set model to evaluation mode
            self.model.eval()
            print("MedGemma loaded successfully!")

        self._meds = [
            "sertraline",
            "fluoxetine",
            "escitalopram",
            "bupropion",
            "venlafaxine",
        ]

        self._symptoms = [
            "depressed mood",
            "anxiety",
            "insomnia",
            "fatigue",
            "poor concentration",
        ]

        self._therapy_terms = ["cbt", "therapy", "counseling"]

    # =========================================================
    # PUBLIC METHODS
    # =========================================================

    def extract_events(self, notes):
        if self.use_real_model:
            return self._extract_events_with_model(notes)
        return self._extract_events_heuristic(notes)

    def extract_assessments(self, notes):
        if self.use_real_model:
            return self._extract_assessments_with_model(notes)
        return self._extract_assessments_heuristic(notes)

    def generate_summary(self, events, assessments, flags):
        if self.use_real_model:
            return self._generate_summary_with_model(events, assessments, flags)

        # Heuristic fallback summary
        meds = [e for e in events if e["type"] == "medication"]
        therapies = [e for e in events if e["type"] == "therapy"]
        symptoms = [e for e in events if e["type"] == "symptom"]

        summary = (
            f"{len(events)} events extracted: "
            f"{len(meds)} medications, "
            f"{len(therapies)} therapy items, "
            f"{len(symptoms)} symptom mentions. "
        )

        if flags:
            summary += f"{len(flags)} attribution uncertainty flag(s) detected."
        else:
            summary += "No attribution uncertainty flags detected."

        return summary

    # =========================================================
    # HEURISTIC MODE (CPU SAFE FALLBACK)
    # =========================================================

    def _extract_events_heuristic(self, notes):
        events = []

        for note in notes:
            text = note["text"]
            note_id = note["note_id"]
            date = note["date"]

            events.extend(self._extract_medications(text, date, note_id))
            events.extend(self._extract_therapies(text, date, note_id))
            events.extend(self._extract_symptoms(text, date, note_id))

        return events

    def _extract_assessments_heuristic(self, notes):
        assessments = []

        for note in notes:
            text = note["text"]
            note_id = note["note_id"]
            date = note["date"]

            for scale in ["PHQ-9", "GAD-7", "MMSE", "MADRS"]:
                match = re.search(rf"{re.escape(scale)}\s*[:=]\s*(\d+)", text)
                if match:
                    assessments.append(
                        {
                            "date": date,
                            "scale": scale,
                            "score": int(match.group(1)),
                            "source_id": note_id,
                            "excerpt": match.group(0),
                        }
                    )

        return assessments

    # =========================================================
    # MODEL MODE (REAL MEDGEMMA WITH FALLBACK)
    # =========================================================

    def _extract_events_with_model(self, notes):
        """Extract events using MedGemma - process one note at a time with fallback"""
        all_events = []

        for note in notes:
            try:
                # Simple prompt for this note
                prompt = f"Extract medications and symptoms from this clinical note:\n{note['text']}\n\nList any medications with doses and symptoms mentioned."

                response = self._call_medgemma_api(prompt)

                # Parse response for events
                events = self._parse_events_from_text(response, note['date'], note['note_id'])
                all_events.extend(events)

            except Exception as e:
                print(f"Error processing note {note['note_id']} with model: {e}")
                print("Falling back to heuristic extraction for this note...")
                # Fall back to heuristic for this note
                all_events.extend(self._extract_medications(note['text'], note['date'], note['note_id']))
                all_events.extend(self._extract_therapies(note['text'], note['date'], note['note_id']))
                all_events.extend(self._extract_symptoms(note['text'], note['date'], note['note_id']))

        return all_events

    def _extract_assessments_with_model(self, notes):
        """Assessments are structured - use heuristic (works better than model)"""
        return self._extract_assessments_heuristic(notes)

    def _generate_summary_with_model(self, events, assessments, flags):
        """Generate summary using MedGemma"""
        try:
            prompt = f"Summarize these clinical findings in 2-3 sentences:\n- {len(events)} events documented\n- {len(assessments)} assessment scores\n- {len(flags)} attribution uncertainty periods"
            return self._call_medgemma_api(prompt)
        except Exception as e:
            print(f"Error generating summary with model: {e}")
            print("Using heuristic summary...")
            return self.generate_summary(events, assessments, flags)

    # =========================================================
    # CORE MODEL CALLING (FIXED FOR CUDA)
    # =========================================================

    def _call_medgemma_api(self, prompt):
        """Call MedGemma with CUDA-safe parameters"""
        if not self.use_real_model or self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not initialized")

        # Format with chat template if available
        if hasattr(self.tokenizer, 'apply_chat_template'):
            messages = [{"role": "user", "content": prompt}]
            try:
                formatted_prompt = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            except:
                formatted_prompt = prompt
        else:
            formatted_prompt = prompt

        # Tokenize input
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        ).to(self.model.device)

        # Generate with CUDA-safe parameters
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=128,  # Short responses
                do_sample=False,  # CRITICAL: Greedy decoding avoids CUDA sampling errors
                num_beams=1,  # No beam search
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove prompt from response
        if formatted_prompt in response:
            response = response.replace(formatted_prompt, "").strip()

        return response

    def _parse_events_from_text(self, text, date, note_id):
        """Parse medications and symptoms from model response"""
        events = []

        # Look for medication patterns in response
        for med in self._meds:
            if med.lower() in text.lower():
                dose_match = re.search(rf"{med}[^.\n]*?(\d+\s?mg)", text, re.IGNORECASE)
                if dose_match:
                    events.append({
                        "date": date,
                        "type": "medication",
                        "label": f"{med.title()} {dose_match.group(1)}",
                        "excerpt": dose_match.group(0),
                        "source_id": note_id,
                    })

        # Look for symptoms in response
        for symptom in self._symptoms:
            if symptom.lower() in text.lower():
                events.append({
                    "date": date,
                    "type": "symptom",
                    "label": symptom.title(),
                    "excerpt": symptom,
                    "source_id": note_id,
                })

        return events

    # =========================================================
    # REGEX HELPERS (HEURISTIC EXTRACTION)
    # =========================================================

    def _extract_medications(self, text, date, note_id):
        events = []
        for med in self._meds:
            match = re.search(rf"\b{med}\b[^.\n]*?(\d+\s?mg)", text, re.IGNORECASE)
            if match:
                dose = match.group(1)
                excerpt = match.group(0)
                events.append(
                    {
                        "date": date,
                        "type": "medication",
                        "label": f"{med.title()} {dose}",
                        "excerpt": excerpt,
                        "source_id": note_id,
                    }
                )
        return events

    def _extract_therapies(self, text, date, note_id):
        events = []
        for term in self._therapy_terms:
            match = re.search(rf"\b{term}\b[^.\n]*", text, re.IGNORECASE)
            if match:
                excerpt = match.group(0)
                label = "CBT" if "cbt" in excerpt.lower() else "Therapy"
                events.append(
                    {
                        "date": date,
                        "type": "therapy",
                        "label": label,
                        "excerpt": excerpt,
                        "source_id": note_id,
                    }
                )
        return events

    def _extract_symptoms(self, text, date, note_id):
        events = []
        for symptom in self._symptoms:
            match = re.search(rf"\b{re.escape(symptom)}\b", text, re.IGNORECASE)
            if match:
                if re.search(rf"denies\s+{re.escape(symptom)}", text, re.IGNORECASE):
                    continue
                events.append(
                    {
                        "date": date,
                        "type": "symptom",
                        "label": symptom.title(),
                        "excerpt": match.group(0),
                        "source_id": note_id,
                    }
                )
        return events