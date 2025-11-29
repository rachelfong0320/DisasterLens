"use client"

import { useState } from "react"
import Header from "@/components/header"
import Footer from "@/components/footer"
import Link from "next/link"

export default function SubscriptionPage() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "annual">("monthly")

  const plans = [
    {
      name: "Basic",
      price: billingCycle === "monthly" ? 29 : 290,
      description: "Perfect for individuals and small research teams",
      features: [
        "Access to real-time disaster data",
        "Up to 10 downloads per month",
        "CSV and JSON export formats",
        "Email support",
        "7-day data retention",
        "Basic filtering capabilities",
      ],
      cta: "Start Free Trial",
      featured: false,
    },
    {
      name: "Professional",
      price: billingCycle === "monthly" ? 79 : 790,
      description: "Ideal for organizations and research institutions",
      features: [
        "All Basic features",
        "Unlimited downloads",
        "All export formats including raw data",
        "Priority email support",
        "90-day data retention",
        "Advanced filtering and custom queries",
        "API access with rate limits",
        "Monthly data analysis reports",
      ],
      cta: "Start Free Trial",
      featured: true,
    },
    {
      name: "Enterprise",
      price: "Custom",
      description: "For large-scale operations and critical infrastructure",
      features: [
        "All Professional features",
        "Unlimited data retention",
        "Dedicated account manager",
        "Phone and priority support",
        "Custom API endpoints",
        "Real-time data streaming",
        "SLA guarantees",
        "Custom integrations",
        "On-premise deployment option",
      ],
      cta: "Contact Sales",
      featured: false,
    },
  ]

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Header onFilterClick={() => {}} />

      <div className="flex-1">
        {/* Hero Section */}
        <section className="bg-gradient-to-r from-primary to-primary/80 text-primary-foreground py-12 md:py-16">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-balance">Simple, Transparent Pricing</h1>
            <p className="text-lg text-primary-foreground/90 mb-8 max-w-2xl mx-auto">
              Choose the perfect plan for your disaster data analysis needs. All plans include 14-day free trial.
            </p>

            {/* Billing Toggle */}
            <div className="flex items-center justify-center gap-4 bg-white/10 rounded-full p-1 w-fit mx-auto">
              <button
                onClick={() => setBillingCycle("monthly")}
                className={`px-6 py-2 rounded-full font-medium transition ${
                  billingCycle === "monthly" ? "bg-white text-primary" : "text-white hover:bg-white/20"
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle("annual")}
                className={`px-6 py-2 rounded-full font-medium transition ${
                  billingCycle === "annual" ? "bg-white text-primary" : "text-white hover:bg-white/20"
                }`}
              >
                Annual (Save 17%)
              </button>
            </div>
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="py-12 md:py-16">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-3 gap-8">
              {plans.map((plan, index) => (
                <div
                  key={index}
                  className={`relative rounded-lg border transition-all duration-300 ${
                    plan.featured
                      ? "md:scale-105 bg-primary text-primary-foreground border-primary shadow-xl"
                      : "bg-card border-border text-foreground"
                  }`}
                >
                  {plan.featured && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-accent text-accent-foreground px-4 py-1 rounded-full text-sm font-semibold">
                      Most Popular
                    </div>
                  )}

                  <div className="p-8">
                    {/* Plan Header */}
                    <h3 className={`text-2xl font-bold mb-2 ${plan.featured ? "" : "text-foreground"}`}>{plan.name}</h3>
                    <p
                      className={`text-sm mb-6 ${plan.featured ? "text-primary-foreground/90" : "text-muted-foreground"}`}
                    >
                      {plan.description}
                    </p>

                    {/* Price */}
                    <div className="mb-6">
                      <div className="flex items-baseline gap-2">
                        <span className={`text-4xl font-bold ${plan.featured ? "" : "text-foreground"}`}>
                          {typeof plan.price === "string" ? plan.price : `$${plan.price}`}
                        </span>
                        {typeof plan.price === "number" && (
                          <span className={`${plan.featured ? "text-primary-foreground/80" : "text-muted-foreground"}`}>
                            /{billingCycle === "monthly" ? "month" : "year"}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* CTA Button */}
                    <button
                      className={`w-full px-4 py-3 font-semibold rounded-md mb-8 transition ${
                        plan.featured
                          ? "bg-white text-primary hover:bg-white/90"
                          : "bg-primary text-primary-foreground hover:opacity-90"
                      }`}
                    >
                      {plan.cta}
                    </button>

                    {/* Features */}
                    <div className="space-y-4">
                      <p
                        className={`text-sm font-semibold ${plan.featured ? "text-primary-foreground/90" : "text-muted-foreground"}`}
                      >
                        What&apos;s included:
                      </p>
                      <ul className="space-y-3">
                        {plan.features.map((feature, featureIndex) => (
                          <li
                            key={featureIndex}
                            className={`flex items-start gap-3 text-sm ${
                              plan.featured ? "text-primary-foreground/95" : ""
                            }`}
                          >
                            <span className="mt-1">✓</span>
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* FAQ Section */}
            <div className="mt-16 max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold text-foreground mb-8 text-center">Frequently Asked Questions</h2>
              <div className="space-y-4">
                {[
                  {
                    q: "Can I upgrade or downgrade my plan?",
                    a: "Yes, you can change your plan anytime. Changes take effect at the start of your next billing cycle.",
                  },
                  {
                    q: "What payment methods do you accept?",
                    a: "We accept all major credit cards, wire transfers, and purchase orders for Enterprise plans.",
                  },
                  {
                    q: "Is there a long-term commitment?",
                    a: "No, all our plans are month-to-month. You can cancel anytime with no penalties.",
                  },
                  {
                    q: "Do you offer academic discounts?",
                    a: "Yes! Educational institutions and non-profits get 50% off. Contact our sales team for details.",
                  },
                ].map((item, index) => (
                  <details key={index} className="group bg-card border border-border rounded-lg p-4">
                    <summary className="flex cursor-pointer justify-between font-semibold text-foreground group-open:text-primary">
                      {item.q}
                      <span className="transition group-open:rotate-180">▼</span>
                    </summary>
                    <p className="mt-4 text-muted-foreground text-sm">{item.a}</p>
                  </details>
                ))}
              </div>
            </div>

            {/* Bottom CTA */}
            <div className="mt-16 text-center">
              <p className="text-muted-foreground mb-4">Have questions about our plans?</p>
              <Link
                href="/"
                className="inline-block px-8 py-3 bg-primary text-primary-foreground font-semibold rounded-md hover:opacity-90 transition"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </section>
      </div>

      <Footer />
    </main>
  )
}
