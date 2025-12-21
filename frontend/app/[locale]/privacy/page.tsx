import PageContainer from "@/components/page-contaner";

export default function PrivacyPage() {
  return (
    <PageContainer title="Privacy Policy">
      <p>
        DisasterLens is a final year academic project developed for educational
        purposes. We respect user privacy and are transparent about the limited
        data we collect.
      </p>

      <h2>Information Collected</h2>
      <p>
        We only collect email addresses. No other personal information is
        collected.
      </p>

      <h2>Purpose of Collection</h2>
      <p>
        Email addresses are used solely for notifications or updates related to
        the platform.
      </p>

      <h2>Data Storage & Security</h2>
      <p>
        Collected emails are stored securely and are not shared with third
        parties.
      </p>

      <h2>Data Removal</h2>
      <p>Users may request removal of their email at any time.</p>

      <h2>Academic Notice</h2>
      <p>
        This project is for educational purposes only and does not operate as a
        commercial service.
      </p>
    </PageContainer>
  );
}
