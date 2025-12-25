import PageContainer from "@/components/page-contaner";
import Image from "next/image";

const team = [
  {
    name: "Rachel Fong Tong Wen",
    role: "Co-Founder / Developer",
    linkedin: "https://www.linkedin.com/in/rachel-fong-tong-wen-4b0329301/",
  },
  {
    name: "Ng Yong Jing",
    role: "Co-Founder / Developer",
    linkedin: "https://www.linkedin.com/in/yong-jing-ng/",
  },
];

export default function TeamPage() {
  return (
    <PageContainer title="Our Team">
      <p className="mb-12 text-sm text-muted-foreground leading-relaxed">
        DisasterLens is developed and maintained by a small independent team.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8">
        {team.map((member) => (
          <div
            key={member.name}
            className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-lg transition-shadow duration-300 flex flex-col items-center text-center"
          >
            {/* Name and Role */}
            <h3 className="font-semibold text-lg text-foreground mb-1">
              {member.name}
            </h3>
            <p className="text-sm text-muted-foreground mb-4">{member.role}</p>

            {/* LinkedIn Link */}
            <a
              href={member.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline font-medium"
            >
              LinkedIn →
            </a>
          </div>
        ))}
      </div>
    </PageContainer>
  );
}
