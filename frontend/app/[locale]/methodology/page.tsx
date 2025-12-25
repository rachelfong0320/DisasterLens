import PageContainer from "@/components/page-contaner";
import DataPipeline from "@/components/DataPipeline";

export default function MethodologyPage() {
  return (
    <PageContainer title="How Our Data Works">
      <div className="space-y-10">
        <section>
          <p className="text-sm text-muted-foreground leading-relaxed">
            DisasterLens aggregates and analyzes disaster-related information
            from publicly available third-party sources to provide situational
            awareness for Malaysia.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">
            Data Collection
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            We retrieve disaster-related data through third-party APIs,
            including services accessed via RapidAPI, as well as publicly
            available sources. All incoming data is treated as raw and
            unverified.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">
            Processing Pipeline
          </h2>
          <DataPipeline />

          <div className="space-y-4 mt-4">
            <div className="flex items-start gap-4">
              <span className="text-primary font-bold text-lg">1.</span>
              <div>
                <h3 className="font-semibold text-primary">Ingestion</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Raw data is fetched at scheduled intervals.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <span className="text-primary font-bold text-lg">2.</span>
              <div>
                <h3 className="font-semibold text-primary">Validation</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  We check for missing fields, invalid timestamps, and malformed
                  locations.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <span className="text-primary font-bold text-lg">3.</span>
              <div>
                <h3 className="font-semibold text-primary">Cleaning</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Duplicate entries and obvious inconsistencies are removed or
                  corrected.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <span className="text-primary font-bold text-lg">4.</span>
              <div>
                <h3 className="font-semibold text-primary">Normalization</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Data is standardized into consistent formats for time,
                  location, and disaster categories.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <span className="text-primary font-bold text-lg">5.</span>
              <div>
                <h3 className="font-semibold text-primary">Storage</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Cleaned data is securely stored in our database for analysis,
                  visualization, and alerts.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-primary">Privacy</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            DisasterLens does not intentionally collect personal data from
            sources. Public content is handled in aggregated form where
            possible.
          </p>
        </section>
      </div>
    </PageContainer>
  );
}
