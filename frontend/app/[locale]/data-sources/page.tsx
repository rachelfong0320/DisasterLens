import PageContainer from "@/components/page-contaner";

export default function DataSourcesPage() {
  return (
    <PageContainer title="Data Sources">
      <h2>Third-Party Providers</h2>
      <p>
        DisasterLens relies on external data providers accessed via third-party
        APIs, including RapidAPI.
      </p>

      <h2>Social Media Signals</h2>
      <p>
        Public posts from platforms such as Instagram and Twitter (X) may be
        analyzed to identify emerging disaster-related signals.
      </p>

      <h2>Data Ownership</h2>
      <p>
        All data remains the property of its original sources. DisasterLens does
        not claim ownership of third-party data.
      </p>

      <h2>Update Frequency</h2>
      <p>
        Update frequency varies depending on API availability, platform limits,
        and network conditions.
      </p>

      <h2>Official Sources</h2>
      <p>
        DisasterLens is not affiliated with government agencies and does not
        replace official emergency communication channels.
      </p>
    </PageContainer>
  );
}
