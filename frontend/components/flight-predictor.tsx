"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon, Plane, CloudRain, Wind, Thermometer } from "lucide-react"
import { format } from "date-fns"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

const destinations = [
  { code: "NYC", name: "New York City", state: "NY" },
  { code: "EWR", name: "Newark", state: "NJ" },
  { code: "SFO", name: "San Francisco", state: "CA" },
  { code: "DTW", name: "Detroit", state: "MI" },
]

export function FlightPredictor() {
  const [date, setDate] = useState<Date>()
  const [destination, setDestination] = useState<string>()
  const [prediction, setPrediction] = useState<{
    delay: number
    weather: { temp: number; wind: number; rain: number }
  } | null>(null)

  const handlePredict = () => {
    // Simulate prediction
    const randomDelay = Math.floor(Math.random() * 100)
    setPrediction({
      delay: randomDelay,
      weather: {
        temp: Math.floor(Math.random() * 30) + 60,
        wind: Math.floor(Math.random() * 20) + 5,
        rain: Math.floor(Math.random() * 100),
      },
    })
  }

  const getDelayStatus = (delay: number) => {
    if (delay < 30) return { label: "Low Risk", variant: "default" as const, color: "text-green-600" }
    if (delay < 60) return { label: "Moderate Risk", variant: "secondary" as const, color: "text-yellow-600" }
    return { label: "High Risk", variant: "destructive" as const, color: "text-red-600" }
  }

  return (
    <section id="predictor" className="py-20">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-4xl">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-balance text-4xl font-bold">Flight Delay Predictor</h2>
            <p className="text-pretty text-muted-foreground leading-relaxed">
              {"Select your flight date and destination to get an AI-powered delay prediction"}
            </p>
          </div>

          <Card className="border-2">
            <CardHeader>
              <CardTitle>Check Your Flight</CardTitle>
              <CardDescription>{"Enter your departure details to analyze delay probability"}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="date">Departure Date</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        id="date"
                        variant="outline"
                        className={cn("w-full justify-start text-left font-normal", !date && "text-muted-foreground")}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, "PPP") : <span>Pick a date</span>}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar mode="single" selected={date} onSelect={setDate} initialFocus />
                    </PopoverContent>
                  </Popover>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="destination">Destination</Label>
                  <Select value={destination} onValueChange={setDestination}>
                    <SelectTrigger id="destination">
                      <SelectValue placeholder="Select destination" />
                    </SelectTrigger>
                    <SelectContent>
                      {destinations.map((dest) => (
                        <SelectItem key={dest.code} value={dest.code}>
                          <div className="flex items-center gap-2">
                            <Plane className="h-4 w-4" />
                            {dest.name}, {dest.state}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button onClick={handlePredict} disabled={!date || !destination} className="w-full" size="lg">
                Predict Delay Likelihood
              </Button>

              {prediction && (
                <div className="space-y-4 rounded-lg border-2 border-primary/20 bg-muted/50 p-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-card-foreground">Prediction Results</h3>
                    <Badge variant={getDelayStatus(prediction.delay).variant}>
                      {getDelayStatus(prediction.delay).label}
                    </Badge>
                  </div>

                  <div className="text-center">
                    <div className="mb-2 text-5xl font-bold text-primary">{prediction.delay}%</div>
                    <p className="text-sm text-muted-foreground">Delay Probability</p>
                  </div>

                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="flex items-center gap-3 rounded-md border bg-card p-3">
                      <Thermometer className="h-5 w-5 text-orange-500" />
                      <div>
                        <p className="text-xs text-muted-foreground">Temperature</p>
                        <p className="font-semibold text-card-foreground">{prediction.weather.temp}°F</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 rounded-md border bg-card p-3">
                      <Wind className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="text-xs text-muted-foreground">Wind Speed</p>
                        <p className="font-semibold text-card-foreground">{prediction.weather.wind} mph</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 rounded-md border bg-card p-3">
                      <CloudRain className="h-5 w-5 text-cyan-500" />
                      <div>
                        <p className="text-xs text-muted-foreground">Rain Chance</p>
                        <p className="font-semibold text-card-foreground">{prediction.weather.rain}%</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  )
}
