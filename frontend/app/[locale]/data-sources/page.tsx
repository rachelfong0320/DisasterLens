import PageContainer from "@/components/page-contaner";

export default function DataSourcesPage() {
  return (
    <PageContainer title="Data Sources">
      <div className="space-y-8">
        <section>
          <h2 className="text-2xl font-semibold text-primary mb-2">
            Third-Party Providers
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            DisasterLens relies on external data providers accessed via
            third-party APIs, including RapidAPI.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-primary mb-2">
            Social Media Signals
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Public posts from platforms such as Instagram and Twitter (X) may be
            analyzed to identify emerging disaster-related signals.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-primary mb-2">
            Data Ownership
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            All data remains the property of its original sources. DisasterLens
            does not claim ownership of third-party data.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-primary mb-2">
            Update Frequency
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Update frequency varies depending on API availability, platform
            limits, and network conditions.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-primary mb-2">
            Official Sources
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            DisasterLens is not affiliated with government agencies and does not
            replace official emergency communication channels.
          </p>
        </section>
      </div>
    </PageContainer>
  );
}
