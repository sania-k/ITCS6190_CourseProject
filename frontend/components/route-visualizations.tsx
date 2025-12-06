"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Plane, ArrowRight } from "lucide-react"

const routes = [
  { from: "CLT", to: "NYC", flights: 45, delay: "Low", color: "bg-green-500" },
  { from: "CLT", to: "EWR", flights: 32, delay: "Moderate", color: "bg-yellow-500" },
  { from: "CLT", to: "SFO", flights: 28, delay: "High", color: "bg-red-500" },
  { from: "CLT", to: "DTW", flights: 38, delay: "Low", color: "bg-green-500" },
]

export function RouteVisualizations() {
  return (
    <section id="routes" className="bg-muted/30 py-20">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-5xl">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-balance text-4xl font-bold">Route Analytics</h2>
            <p className="text-pretty text-muted-foreground leading-relaxed">
              {"Live tracking of CLT departures and their delay patterns"}
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {routes.map((route) => (
              <Card key={route.to} className="overflow-hidden transition-shadow hover:shadow-lg">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">
                      {route.from} → {route.to}
                    </CardTitle>
                    <div className={`h-3 w-3 rounded-full ${route.color}`} />
                  </div>
                  <CardDescription>Daily route status</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                          <Plane className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-foreground">{route.flights}</p>
                          <p className="text-sm text-muted-foreground">Daily Flights</p>
                        </div>
                      </div>
                      <ArrowRight className="h-8 w-8 text-muted-foreground" />
                    </div>

                    <div className="flex items-center justify-between rounded-md border bg-card/50 p-3">
                      <span className="text-sm font-medium text-card-foreground">Delay Status:</span>
                      <span
                        className={cn(
                          "text-sm font-semibold",
                          route.delay === "Low" && "text-green-600",
                          route.delay === "Moderate" && "text-yellow-600",
                          route.delay === "High" && "text-red-600",
                        )}
                      >
                        {route.delay} Risk
                      </span>
                    </div>

                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className={`h-full ${route.color}`}
                        style={{
                          width: `${route.delay === "Low" ? "30" : route.delay === "Moderate" ? "60" : "90"}%`,
                        }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="mt-8 border-2 border-primary/20">
            <CardHeader>
              <CardTitle>Route Map Visualization</CardTitle>
              <CardDescription>Interactive map showing all CLT departures</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative aspect-video overflow-hidden rounded-lg border-2 bg-gradient-to-br from-primary/5 to-secondary/5">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-primary">
                      <Plane className="h-10 w-10 text-primary-foreground" />
                    </div>
                    <p className="text-xl font-semibold text-foreground">CLT Airport</p>
                    <p className="text-sm text-muted-foreground">Charlotte, North Carolina</p>
                  </div>
                </div>

                {/* Animated flight paths */}
                <svg className="absolute inset-0 h-full w-full">
                  <path
                    d="M 250 200 Q 400 100 600 150"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    className="text-primary/30"
                    strokeDasharray="5,5"
                  />
                  <path
                    d="M 250 200 Q 150 150 100 250"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    className="text-secondary/30"
                    strokeDasharray="5,5"
                  />
                  <path
                    d="M 250 200 Q 350 300 500 350"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    className="text-accent/30"
                    strokeDasharray="5,5"
                  />
                </svg>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ")
}
