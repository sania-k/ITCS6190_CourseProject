import { Card, CardContent } from "@/components/ui/card"
import { Target, Database, Brain, Shield } from "lucide-react"

export function AboutSection() {
  return (
    <section id="about" className="py-20">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-5xl">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-balance text-4xl font-bold">About SkyWatch CLT</h2>
            <p className="text-pretty text-muted-foreground leading-relaxed">
              {"Our mission is to provide travelers with accurate, real-time flight delay predictions"}
            </p>
          </div>

          <div className="mb-12 rounded-xl border-2 bg-card p-8 md:p-12">
            <h3 className="mb-6 text-2xl font-bold text-card-foreground">The Problem We Solve</h3>
            <p className="mb-4 leading-relaxed text-card-foreground">
              {
                "Flight delays cost travelers billions in lost time and money annually. Weather conditions are the leading cause of delays, yet passengers often learn about delays only when they arrive at the airport."
              }
            </p>
            <p className="leading-relaxed text-card-foreground">
              {
                "SkyWatch CLT bridges this gap by analyzing historical flight data, current weather patterns, and machine learning algorithms to predict delays before they happen, giving you the power to plan ahead."
              }
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Card className="border-2">
              <CardContent className="flex gap-4 p-6">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <Target className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h4 className="mb-2 font-semibold text-card-foreground">Our Approach</h4>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {
                      "We combine real-time weather data from Charlotte-Douglas Airport with historical delay patterns to generate accurate predictions."
                    }
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardContent className="flex gap-4 p-6">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-secondary/10">
                  <Database className="h-6 w-6 text-secondary" />
                </div>
                <div>
                  <h4 className="mb-2 font-semibold text-card-foreground">Data Sources</h4>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {
                      "Integration with FAA flight data, NOAA weather services, and airport operational metrics ensures comprehensive analysis."
                    }
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardContent className="flex gap-4 p-6">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-accent/10">
                  <Brain className="h-6 w-6 text-accent" />
                </div>
                <div>
                  <h4 className="mb-2 font-semibold text-card-foreground">AI Technology</h4>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {
                      "Machine learning models trained on years of flight and weather data provide increasingly accurate predictions over time."
                    }
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardContent className="flex gap-4 p-6">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-chart-4/10">
                  <Shield className="h-6 w-6 text-chart-4" />
                </div>
                <div>
                  <h4 className="mb-2 font-semibold text-card-foreground">Value Delivered</h4>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {
                      "Empower travelers to make informed decisions, reduce airport wait times, and minimize travel stress with proactive insights."
                    }
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  )
}
