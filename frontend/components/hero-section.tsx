import { CloudRain, Clock, TrendingUp } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden border-b bg-gradient-to-b from-background to-muted/20 py-20">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="mb-6 text-balance text-5xl font-bold tracking-tight md:text-6xl">
            {"Predict Flight Delays with"} <span className="text-primary">Weather Intelligence</span>
          </h1>
          <p className="mb-8 text-pretty text-lg text-muted-foreground leading-relaxed">
            {
              "SkyWatch CLT analyzes real-time weather conditions at Charlotte-Douglas Airport to predict flight delays before they happen. Make informed travel decisions with confidence."
            }
          </p>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            <div className="flex flex-col items-center gap-3 rounded-lg border bg-card p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <CloudRain className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold text-card-foreground">Weather Analysis</h3>
              <p className="text-sm text-muted-foreground text-balance">{"Real-time weather data integration"}</p>
            </div>

            <div className="flex flex-col items-center gap-3 rounded-lg border bg-card p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary/10">
                <Clock className="h-6 w-6 text-secondary" />
              </div>
              <h3 className="font-semibold text-card-foreground">Delay Predictions</h3>
              <p className="text-sm text-muted-foreground text-balance">{"AI-powered likelihood estimates"}</p>
            </div>

            <div className="flex flex-col items-center gap-3 rounded-lg border bg-card p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10">
                <TrendingUp className="h-6 w-6 text-accent" />
              </div>
              <h3 className="font-semibold text-card-foreground">Route Analytics</h3>
              <p className="text-sm text-muted-foreground text-balance">{"Comprehensive flight tracking"}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
