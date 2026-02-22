from attribution import detect_attribution_uncertainty


class NeuroBriefPipeline:
    def __init__(self, medgemma_client):
        self.medgemma = medgemma_client

    def process_case(self, notes):
        events = self.medgemma.extract_events(notes)
        assessments = self.medgemma.extract_assessments(notes)

        flags = detect_attribution_uncertainty(
            events=events,
            assessments=assessments,
            window_days=28,
            min_delta=1,
        )

        summary = self.medgemma.generate_summary(events, assessments, flags)

        return {
            "events": events,
            "assessments": assessments,
            "flags": flags,
            "summary": summary,
        }
