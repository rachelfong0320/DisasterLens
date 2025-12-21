import PageContainer from "@/components/page-contaner";

export default function DisclaimerPage() {
  return (
    <PageContainer title="Academic Disclaimer">
      <p>
        DisasterLens is a <strong>final year academic project</strong> developed
        for educational purposes. It is{" "}
        <strong>not an official emergency service</strong> and is{" "}
        <strong>not affiliated with any government agency</strong>.
      </p>

      <h2>Not for Emergency Use</h2>
      <p>
        Information provided should <strong>not</strong> be relied upon for
        emergency response. Always consult official government channels for
        disaster guidance.
      </p>

      <h2>Data Limitations</h2>
      <p>Data may be delayed, incomplete, inaccurate, or subject to change.</p>

      <h2>Liability</h2>
      <p>
        Use of the platform is at the user’s own risk. DisasterLens takes no
        responsibility for decisions made based on this data.
      </p>
    </PageContainer>
  );
}
