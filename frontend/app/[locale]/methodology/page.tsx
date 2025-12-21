import PageContainer from "@/components/page-contaner";
import DataPipeline from "@/components/DataPipeline";

export default function MethodologyPage() {
  return (
    <PageContainer title="How Our Data Works">
      <p>
        DisasterLens aggregates and analyzes disaster-related information from
        publicly available third-party sources to provide situational awareness
        for Malaysia.
      </p>

      <h2>Data Collection</h2>
      <p>
        We retrieve disaster-related data through third-party APIs, including
        services accessed via RapidAPI, as well as publicly available sources.
        All incoming data is treated as raw and unverified.
      </p>

      <h2>Processing Pipeline</h2>
      <DataPipeline />

      <h3>1. Ingestion</h3>
      <p>Raw data is fetched at scheduled intervals.</p>

      <h3>2. Validation</h3>
      <p>
        We check for missing fields, invalid timestamps, and malformed
        locations.
      </p>

      <h3>3. Cleaning</h3>
      <p>
        Duplicate entries and obvious inconsistencies are removed or corrected.
      </p>

      <h3>4. Normalization</h3>
      <p>
        Data is standardized into consistent formats for time, location, and
        disaster categories.
      </p>

      <h3>5. Storage</h3>
      <p>
        Cleaned data is securely stored in our database for analysis,
        visualization, and alerts.
      </p>

      <h2>Privacy</h2>
      <p>
        DisasterLens does not intentionally collect personal data from sources.
        Public content is handled in aggregated form where possible.
      </p>
    </PageContainer>
  );
}
