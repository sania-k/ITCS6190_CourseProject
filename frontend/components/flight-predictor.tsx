// // "use client"

// // import { useState, useEffect } from "react"
// // import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
// // import { Label } from "@/components/ui/label"
// // import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
// // import { Button } from "@/components/ui/button"
// // import { Calendar } from "@/components/ui/calendar"
// // import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
// // import { CalendarIcon, Plane, CloudRain, Wind, Thermometer } from "lucide-react"
// // import { format } from "date-fns"
// // import { cn } from "@/lib/utils"
// // import { Badge } from "@/components/ui/badge"

// // const API = process.env.NEXT_PUBLIC_BACKEND_URL

// // export function FlightPredictor() {
// //   const [destination, setDestination] = useState<string>("")
// //   const [validDates, setValidDates] = useState<string[]>([])
// //   const [date, setDate] = useState<Date>()
// //   const [validFlights, setValidFlights] = useState<any[]>([])
// //   const [selectedFlight, setSelectedFlight] = useState<string>("")

// //   const [prediction, setPrediction] = useState<{
// //     delay: number
// //     weather: { temp: number; wind: number; rain: number }
// //   } | null>(null)

// //   // -------------------------------
// //   // 1. Fetch valid dates when destination changes
// //   // -------------------------------
// //   useEffect(() => {
// //     if (!destination) return
// //     setValidDates([])
// //     setDate(undefined)
// //     setValidFlights([])
// //     setSelectedFlight("")

// //     fetch(`${API}/dates?arrival=${destination}`)
// //       .then(r => r.json())
// //       .then(dates => setValidDates(dates))
// //   }, [destination])

// //   // -------------------------------
// //   // 2. Fetch valid flights when date changes
// //   // -------------------------------
// //   useEffect(() => {
// //     if (!destination || !date) return
// //     setValidFlights([])
// //     setSelectedFlight("")

// //     const formatted = format(date, "yyyy-MM-dd")

// //     fetch(`${API}/flights?arrival=${destination}&date=${formatted}`)
// //       .then(r => r.json())
// //       .then(list => setValidFlights(list))
// //   }, [date, destination])


// //   // -------------------------------
// //   // 3. Predict
// //   // -------------------------------
// //   const handlePredict = () => {
// //     if (!selectedFlight) return

// //     fetch(`${API}/predict?flight_id=${selectedFlight}`)
// //       .then(r => r.json())
// //       .then(data => setPrediction(data))
// //   }

// //   const getDelayStatus = (delay: number) => {
// //     if (delay < 30) return { label: "Low Risk", variant: "default" as const, color: "text-green-600" }
// //     if (delay < 60) return { label: "Moderate Risk", variant: "secondary" as const, color: "text-yellow-600" }
// //     return { label: "High Risk", variant: "destructive" as const, color: "text-red-600" }
// //   }

// //   return (
// //     <section id="predictor" className="py-20">
// //       <div className="container mx-auto px-4">
// //         <div className="mx-auto max-w-4xl">
// //           <div className="mb-12 text-center">
// //             <h2 className="mb-4 text-balance text-4xl font-bold">Flight Delay Predictor</h2>
// //             <p className="text-pretty text-muted-foreground leading-relaxed">
// //               Select a destination, date, and flight to get an AI-powered delay prediction.
// //             </p>
// //           </div>

// //           <Card className="border-2">
// //             <CardHeader>
// //               <CardTitle>Check Your Flight</CardTitle>
// //               <CardDescription>Enter your details to analyze delay probability</CardDescription>
// //             </CardHeader>

// //             <CardContent className="space-y-6">
// //               {/* DESTINATION */}
// //               <div className="space-y-2">
// //                 <Label>Destination</Label>
// //                 <Select value={destination} onValueChange={setDestination}>
// //                   <SelectTrigger>
// //                     <SelectValue placeholder="Select destination" />
// //                   </SelectTrigger>
// //                   <SelectContent>
// //                     <SelectItem value="EWR">Newark, NJ</SelectItem>
// //                     <SelectItem value="NYC">New York, NY</SelectItem>
// //                     <SelectItem value="SFO">San Francisco, CA</SelectItem>
// //                     <SelectItem value="DTW">Detroit, MI</SelectItem>
// //                   </SelectContent>
// //                 </Select>
// //               </div>

// //               {/* DATE PICKER (ONLY ENABLED AFTER DESTINATION) */}
// //               <div className="space-y-2 opacity-100">
// //                 <Label>Departure Date</Label>
// //                 <Popover>
// //                   <PopoverTrigger asChild>
// //                     <Button
// //                       variant="outline"
// //                       disabled={!destination}
// //                       className="w-full justify-start text-left font-normal"
// //                     >
// //                       <CalendarIcon className="mr-2 h-4 w-4" />
// //                       {date ? format(date, "PPP") : <span>Select valid date</span>}
// //                     </Button>
// //                   </PopoverTrigger>

// //                   <PopoverContent className="w-auto p-0" align="start">
// //                     <Calendar
// //                       mode="single"
// //                       selected={date}
// //                       onSelect={setDate}
// //                       disabled={(d) => !validDates.includes(format(d, "yyyy-MM-dd"))}
// //                     />
// //                   </PopoverContent>
// //                 </Popover>
// //               </div>

// //               {/* FLIGHT SELECTOR (ONLY ENABLED AFTER DATE) */}
// //               <div className="space-y-2">
// //                 <Label>Flight</Label>
// //                 <Select 
// //                   value={selectedFlight} 
// //                   onValueChange={setSelectedFlight}
// //                   disabled={validFlights.length === 0}
// //                 >
// //                   <SelectTrigger>
// //                     <SelectValue placeholder="Select valid flight" />
// //                   </SelectTrigger>
// //                   <SelectContent>
// //                     {validFlights.map((f) => (
// //                       <SelectItem key={f.flight_id} value={f.flight_id}>
// //                         {f.departure_time} → {f.arrival_time} (Flight {f.flight_id})
// //                       </SelectItem>
// //                     ))}
// //                   </SelectContent>
// //                 </Select>
// //               </div>

// //               {/* PREDICT BUTTON */}
// //               <Button 
// //                 onClick={handlePredict}
// //                 disabled={!selectedFlight}
// //                 className="w-full"
// //                 size="lg"
// //               >
// //                 Predict Delay
// //               </Button>

// //               {/* RESULT SECTION (unchanged except for logic) */}
// //               {prediction && (
// //                 <div className="space-y-4 rounded-lg border-2 border-primary/20 bg-muted/50 p-6">
// //                   <div className="flex items-center justify-between">
// //                     <h3 className="text-lg font-semibold text-card-foreground">Prediction Results</h3>
// //                     <Badge variant={getDelayStatus(prediction.delay).variant}>
// //                       {getDelayStatus(prediction.delay).label}
// //                     </Badge>
// //                   </div>

// //                   <div className="text-center">
// //                     <div className="mb-2 text-5xl font-bold text-primary">{prediction.delay}%</div>
// //                     <p className="text-sm text-muted-foreground">Delay Probability</p>
// //                   </div>

// //                   <div className="grid gap-4 md:grid-cols-3">
// //                     <div className="flex items-center gap-3 rounded-md border bg-card p-3">
// //                       <Thermometer className="h-5 w-5 text-orange-500" />
// //                       <div>
// //                         <p className="text-xs text-muted-foreground">Temperature</p>
// //                         <p className="font-semibold text-card-foreground">
// //                           {prediction.weather.temp}°F
// //                         </p>
// //                       </div>
// //                     </div>

// //                     <div className="flex items-center gap-3 rounded-md border bg-card p-3">
// //                       <Wind className="h-5 w-5 text-blue-500" />
// //                       <div>
// //                         <p className="text-xs text-muted-foreground">Wind Speed</p>
// //                         <p className="font-semibold text-card-foreground">
// //                           {prediction.weather.wind} mph
// //                         </p>
// //                       </div>
// //                     </div>

// //                     <div className="flex items-center gap-3 rounded-md border bg-card p-3">
// //                       <CloudRain className="h-5 w-5 text-cyan-500" />
// //                       <div>
// //                         <p className="text-xs text-muted-foreground">Rain Chance</p>
// //                         <p className="font-semibold text-card-foreground">
// //                           {prediction.weather.rain}%
// //                         </p>
// //                       </div>
// //                     </div>
// //                   </div>
// //                 </div>
// //               )}
// //             </CardContent>
// //           </Card>
// //         </div>
// //       </div>
// //     </section>
// //   )
// // }

























// "use client"

// import { useState, useRef, useEffect } from "react"
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
// import { Label } from "@/components/ui/label"
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
// import { Button } from "@/components/ui/button"
// import { Calendar } from "@/components/ui/calendar"
// import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
// // import { CalendarIcon, Plane, CloudRain, Wind, Thermometer } from "lucide-react"
// import { CalendarIcon} from "lucide-react"
// import { format } from "date-fns"
// import { Badge } from "@/components/ui/badge"

// const API = process.env.NEXT_PUBLIC_BACKEND_URL

// export function FlightPredictor() {
//   // ------------------------------------------------------------
//   // CACHES
//   // ------------------------------------------------------------
//   const datesCache = useRef<{ [dest: string]: string[] }>({})
//   const flightsCache = useRef<{ [key: string]: any[] }>({})

//   // ------------------------------------------------------------
//   // STATE
//   // ------------------------------------------------------------
//   const [destination, setDestination] = useState("")
//   const [validDates, setValidDates] = useState<string[]>([])
//   const [date, setDate] = useState<Date>()
//   const [validFlights, setValidFlights] = useState<any[]>([])
//   const [selectedFlight, setSelectedFlight] = useState("")
//   // const [prediction, setPrediction] = useState<
//   //   { delay: number; weather: { temp: number; wind: number; rain: number } } | null
//   // >(null)
//   const [prediction, setPrediction] = useState<{ delay: number } | null>(null)

//   // ------------------------------------------------------------
//   // Fetch dates when destination changes
//   // ------------------------------------------------------------
//   useEffect(() => {
//     if (!destination) return

//     setValidDates([])
//     setDate(undefined)
//     setValidFlights([])
//     setSelectedFlight("")

//     // CACHE HIT
//     if (datesCache.current[destination]) {
//       setValidDates(datesCache.current[destination])
//       return
//     }

//     // CACHE MISS
//     fetch(`${API}/dates?arrival=${destination}`)
//       .then((r) => r.json())
//       .then((data) => {
//         datesCache.current[destination] = data
//         setValidDates(data)
//       })
//   }, [destination])

//   // ------------------------------------------------------------
//   // Fetch flights when date changes
//   // ------------------------------------------------------------
//   useEffect(() => {
//     if (!destination || !date) return

//     const formatted = format(date, "yyyy-MM-dd")
//     const key = `${destination}-${formatted}`

//     setValidFlights([])
//     setSelectedFlight("")

//     // CACHE HIT
//     if (flightsCache.current[key]) {
//       setValidFlights(flightsCache.current[key])
//       return
//     }

//     // CACHE MISS
//     fetch(`${API}/flights?arrival=${destination}&date=${formatted}`)
//       .then((r) => r.json())
//       .then((list) => {
//         flightsCache.current[key] = list
//         setValidFlights(list)
//       })
//   }, [date, destination])

//   // ------------------------------------------------------------
//   // Predict
//   // ------------------------------------------------------------
//   const handlePredict = () => {
//     if (!selectedFlight) return

//     fetch(`${API}/predict?flight_id=${selectedFlight}`)
//       .then((r) => r.json())
//       .then((data) => setPrediction(data))
//   }

//   const getDelayStatus = (delay: number) => {
//     if (delay < 30) return { label: "Low Risk", variant: "default" as const }
//     if (delay < 60) return { label: "Moderate Risk", variant: "secondary" as const }
//     return { label: "High Risk", variant: "destructive" as const }
//   }

//   // ------------------------------------------------------------
//   // UI RETURN (FULLY RESTORED)
//   // ------------------------------------------------------------
//   return (
//     <section id="predictor" className="py-20">
//       <div className="container mx-auto px-4">
//         <div className="mx-auto max-w-4xl">
//           <div className="mb-12 text-center">
//             <h2 className="mb-4 text-balance text-4xl font-bold">Flight Delay Predictor</h2>
//             <p className="text-pretty text-muted-foreground leading-relaxed">
//               Select a destination, date, and flight to get an AI-powered delay prediction.
//             </p>
//           </div>

//           <Card className="border-2">
//             <CardHeader>
//               <CardTitle>Check Your Flight</CardTitle>
//               <CardDescription>Enter your details to analyze delay probability</CardDescription>
//             </CardHeader>

//             <CardContent className="space-y-6">
//               {/* DESTINATION */}
//               <div className="space-y-2">
//                 <Label>Destination</Label>
//                 <Select value={destination} onValueChange={setDestination}>
//                   <SelectTrigger>
//                     <SelectValue placeholder="Select destination" />
//                   </SelectTrigger>
//                   <SelectContent>
//                     <SelectItem value="EWR">Newark, NJ</SelectItem>
//                     <SelectItem value="NYC">New York, NY</SelectItem>
//                     <SelectItem value="SFO">San Francisco, CA</SelectItem>
//                     <SelectItem value="DTW">Detroit, MI</SelectItem>
//                   </SelectContent>
//                 </Select>
//               </div>

//               {/* DATE PICKER */}
//               <div className="space-y-2">
//                 <Label>Departure Date</Label>
//                 <Popover>
//                   <PopoverTrigger asChild>
//                     <Button
//                       variant="outline"
//                       disabled={!destination}
//                       className="w-full justify-start text-left font-normal"
//                     >
//                       <CalendarIcon className="mr-2 h-4 w-4" />
//                       {date ? format(date, "PPP") : <span>Select valid date</span>}
//                     </Button>
//                   </PopoverTrigger>

//                   <PopoverContent className="w-auto p-0" align="start">
//                     <Calendar
//                       mode="single"
//                       selected={date}
//                       onSelect={setDate}
//                       disabled={(d) => !validDates.includes(format(d, "yyyy-MM-dd"))}
//                     />
//                   </PopoverContent>
//                 </Popover>
//               </div>

//               {/* FLIGHTS */}
//               <div className="space-y-2">
//                 <Label>Flight</Label>
//                 <Select
//                   value={selectedFlight}
//                   onValueChange={setSelectedFlight}
//                   disabled={validFlights.length === 0}
//                 >
//                   <SelectTrigger>
//                     <SelectValue placeholder="Select valid flight" />
//                   </SelectTrigger>

//                   <SelectContent>
//                     {validFlights.map((f) => (
//                       <SelectItem key={f.flight_id} value={String(f.flight_id)}>
//                         {f.departure_time} → {f.arrival_time} (Flight {f.flight_id})
//                       </SelectItem>
//                     ))}
//                   </SelectContent>
//                 </Select>
//               </div>

//               {/* PREDICT BUTTON */}
//               <Button onClick={handlePredict} disabled={!selectedFlight} className="w-full" size="lg">
//                 Predict Delay
//               </Button>

//               {/* RESULTS */}
//               {prediction && (
//                 <div className="space-y-4 rounded-lg border-2 border-primary/20 bg-muted/50 p-6">
//                   <div className="flex items-center justify-between">
//                     <h3 className="text-lg font-semibold text-card-foreground">Prediction Results</h3>
//                     <Badge variant={getDelayStatus(prediction.delay).variant}>
//                       {getDelayStatus(prediction.delay).label}
//                     </Badge>
//                   </div>

//                   <div className="text-center">
//                     <div className="mb-2 text-5xl font-bold text-primary">{prediction.delay}%</div>
//                     <p className="text-sm text-muted-foreground">Delay Probability</p>
//                   </div>

//                   {/* WEATHER */}
//                   {/*
//                   <div className="grid gap-4 md:grid-cols-3">
//                     <div className="flex items-center gap-3 rounded-md border bg-card p-3">
//                       <Thermometer className="h-5 w-5 text-orange-500" />
//                       <div>
//                         <p className="text-xs text-muted-foreground">Temperature</p>
//                         <p className="font-semibold text-card-foreground">
//                           {prediction.weather.temp}°F
//                         </p>
//                       </div>
//                     </div>

//                     <div className="flex items-center gap-3 rounded-md border bg-card p-3">
//                       <Wind className="h-5 w-5 text-blue-500" />
//                       <div>
//                         <p className="text-xs text-muted-foreground">Wind Speed</p>
//                         <p className="font-semibold text-card-foreground">
//                           {prediction.weather.wind} mph
//                         </p>
//                       </div>
//                     </div>

//                     <div className="flex items-center gap-3 rounded-md border bg-card p-3">
//                       <CloudRain className="h-5 w-5 text-cyan-500" />
//                       <div>
//                         <p className="text-xs text-muted-foreground">Rain Chance</p>
//                         <p className="font-semibold text-card-foreground">
//                           {prediction.weather.rain}%
//                         </p>
//                       </div>
//                     </div>
                  

//                   </div>
//                   */}
//                 </div>
//               )}
//             </CardContent>
//           </Card>
//         </div>
//       </div>
//     </section>
//   )
// }




















"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectTrigger, SelectValue, SelectItem, SelectContent } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { CalendarIcon } from "lucide-react"
import { format } from "date-fns"

const API = process.env.NEXT_PUBLIC_BACKEND_URL

export function FlightPredictor() {
  const [destinations, setDestinations] = useState<string[]>([])
  const [destination, setDestination] = useState<string>("")

  const [dates, setDates] = useState<string[]>([])
  const [date, setDate] = useState<Date | null>(null)

  const [flights, setFlights] = useState<any[]>([])
  const [flightId, setFlightId] = useState<string>("")

  const [prediction, setPrediction] = useState<number | null>(null)

  // -----------------------------
  // Fetch destinations on load
  // -----------------------------
  useEffect(() => {
    fetch(`${API}/destinations`)
      .then(res => res.json())
      .then(data => setDestinations(data))
  }, [])

  // -----------------------------
  // When destination changes → fetch valid dates
  // -----------------------------
  useEffect(() => {
    if (!destination) return

    setDate(null)
    setFlightId("")
    setFlights([])

    fetch(`${API}/dates?arrival=${encodeURIComponent(destination)}`)
      .then(res => res.json())
      .then(data => setDates(data))
  }, [destination])

  // -----------------------------
  // When date changes → fetch valid flights
  // -----------------------------
  useEffect(() => {
    if (!destination || !date) return

    const formatted = format(date, "yyyy-MM-dd")
    setFlightId("")
    setFlights([])

    fetch(`${API}/flights?arrival=${encodeURIComponent(destination)}&date=${formatted}`)
      .then(res => res.json())
      .then(data => setFlights(data))
  }, [date])

  // -----------------------------
  // Predict delay
  // -----------------------------
  const handlePredict = async () => {
    if (!flightId) return

    const res = await fetch(`${API}/predict?flight_id=${flightId}`)
    const data = await res.json()
    setPrediction(data.delay)
  }

  return (
    <Card className="p-6 max-w-3xl mx-auto mt-10">
      <CardHeader>
        <CardTitle>Check Your Flight</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">

        {/* Destination */}
        <div>
          <Label>Destination</Label>
          <Select
            value={destination}
            onValueChange={setDestination}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select destination" />
            </SelectTrigger>
            <SelectContent>
              {destinations.map((dest) => (
                <SelectItem key={dest} value={dest}>
                  {dest}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Date selection */}
        <div>
          <Label>Departure Date</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-full justify-start">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {date ? format(date, "PPP") : "Select valid date"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar
                mode="single"
                selected={date ?? undefined}
                onSelect={setDate}
                disabled={(day) => {
                  const formatted = format(day, "yyyy-MM-dd")
                  return !dates.includes(formatted)
                }}
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Flights */}
        <div>
          <Label>Flight</Label>
          <Select
            value={flightId}
            onValueChange={setFlightId}
            disabled={flights.length === 0}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select valid flight" />
            </SelectTrigger>
            <SelectContent>
              {flights.map((f) => (
                <SelectItem key={f.flight_id} value={String(f.flight_id)}>
                  Flight #{f.flight_id} — Dep {f.departure_time}, Arr {f.arrival_time}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Predict button */}
        <Button
          className="w-full bg-sky-900 hover:bg-sky-800"
          onClick={handlePredict}
          disabled={!flightId}
        >
          Predict Delay
        </Button>

        {/* Prediction result */}
        {prediction !== null && (
          <div className="text-center text-xl mt-4">
            <strong>
              Delay Prediction: {prediction === 1 ? "Likely Delayed" : "Likely On Time"}
            </strong>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
