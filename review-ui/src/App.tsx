import { useEffect, useMemo, useState } from "react"
import {
  ArrowDownToLine,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleSlash,
  FileText,
  ListChecks,
  Search,
  Split,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

type VoiceSide = {
  label: string
  source: string
  phones: string[]
  phoneString: string
  espeakPayload: string
  audio: string
}

type ReviewItem = {
  id: string
  text: string
  focus: string
  why: string
  old: VoiceSide
  real: VoiceSide
  changed: boolean
}

type ReviewData = {
  title: string
  note: string
  items: ReviewItem[]
}

type FrontendToken = {
  id: number
  raw: string
  normalized: string
  kind: string
  language: string
  semiotic_class: string
  phones: string[]
  source: string
  confidence: string
  status: string
}

type FrontendItem = {
  id: string
  category: string
  input: string
  normalizedText: string
  phoneSequence: string[]
  tokens: FrontendToken[]
  chunks: Array<{
    id: number
    text: string
    boundary_strength: string
    sentence_type: string
    intonation_hint: string
  }>
  warnings: Array<{ code: string; span: string; token_id: number }>
}

type FrontendData = {
  title: string
  generatedBy: string
  profile: string
  items: FrontendItem[]
}

type Vote = "old" | "real" | "tie" | "bad" | ""

type ReviewState = Record<string, { vote: Vote; notes: string }>

const STORAGE_KEY = "nepali-g2p-review-v1"

function loadState(): ReviewState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function App() {
  const [data, setData] = useState<ReviewData | null>(null)
  const [frontendData, setFrontendData] = useState<FrontendData | null>(null)
  const [mode, setMode] = useState<"frontend" | "audio">("frontend")
  const [selectedId, setSelectedId] = useState("")
  const [query, setQuery] = useState("")
  const [filter, setFilter] = useState<"all" | "changed" | "pending">("changed")
  const [reviewState, setReviewState] = useState<ReviewState>(() => loadState())

  useEffect(() => {
    fetch("/review-data.json")
      .then((response) => response.json())
      .then((payload: ReviewData) => {
        setData(payload)
        setSelectedId(payload.items[0]?.id ?? "")
      })
    fetch("/frontend-data.json")
      .then((response) => response.json())
      .then((payload: FrontendData) => setFrontendData(payload))
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviewState))
  }, [reviewState])

  const items = useMemo(() => data?.items ?? [], [data])
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return items.filter((item) => {
      const vote = reviewState[item.id]?.vote ?? ""
      if (filter === "changed" && !item.changed) return false
      if (filter === "pending" && vote) return false
      if (!q) return true
      return (
        item.text.toLowerCase().includes(q) ||
        item.focus.toLowerCase().includes(q) ||
        item.why.toLowerCase().includes(q) ||
        item.old.phoneString.toLowerCase().includes(q) ||
        item.real.phoneString.toLowerCase().includes(q)
      )
    })
  }, [filter, items, query, reviewState])

  const selected = filtered.find((item) => item.id === selectedId) ?? filtered[0]
  const selectedIndex = selected
    ? filtered.findIndex((item) => item.id === selected.id)
    : -1
  const completed = items.filter((item) => reviewState[item.id]?.vote).length
  const changed = items.filter((item) => item.changed).length

  function updateVote(itemId: string, vote: Vote) {
    setReviewState((prev) => ({
      ...prev,
      [itemId]: { vote, notes: prev[itemId]?.notes ?? "" },
    }))
  }

  function updateNotes(itemId: string, notes: string) {
    setReviewState((prev) => ({
      ...prev,
      [itemId]: { vote: prev[itemId]?.vote ?? "", notes },
    }))
  }

  function move(delta: number) {
    if (!filtered.length || selectedIndex < 0) return
    const next =
      filtered[(selectedIndex + delta + filtered.length) % filtered.length]
    setSelectedId(next.id)
  }

  function exportTsv() {
    const header = [
      "id",
      "text",
      "focus",
      "old_phones",
      "real_phones",
      "changed",
      "vote",
      "notes",
    ]
    const lines = [
      header.join("\t"),
      ...items.map((item) => {
        const state = reviewState[item.id] ?? { vote: "", notes: "" }
        return [
          item.id,
          item.text,
          item.focus,
          item.old.phoneString,
          item.real.phoneString,
          item.changed ? "yes" : "no",
          state.vote,
          state.notes.replace(/\s+/g, " ").trim(),
        ].join("\t")
      }),
    ]
    const blob = new Blob([`${lines.join("\n")}\n`], {
      type: "text/tab-separated-values;charset=utf-8",
    })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = "nepali-g2p-review.tsv"
    anchor.click()
    URL.revokeObjectURL(url)
  }

  if (!data || !frontendData) {
    return (
      <main className="flex min-h-svh items-center justify-center bg-background p-6">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>Loading review set</CardTitle>
            <CardDescription>Reading generated eSpeak samples.</CardDescription>
          </CardHeader>
        </Card>
      </main>
    )
  }

  if (!selected) {
    return (
      <main className="flex min-h-svh items-center justify-center bg-background p-6">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>No matches</CardTitle>
            <CardDescription>
              Clear the search or switch filters to continue reviewing.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="outline"
              onClick={() => {
                setQuery("")
                setFilter("all")
              }}
            >
              Reset filters
            </Button>
          </CardContent>
        </Card>
      </main>
    )
  }

  const activeState = reviewState[selected.id] ?? { vote: "", notes: "" }

  if (mode === "frontend") {
    return (
      <FrontendAudit
        data={frontendData}
        mode={mode}
        setMode={setMode}
      />
    )
  }

  return (
    <main className="min-h-svh bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Fixed-vocoder review</Badge>
              <Badge variant="muted">{items.length} words</Badge>
              <Badge variant="muted">{changed} changed</Badge>
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-normal sm:text-3xl">
                Nepali G2P listening review
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                Compare the existing frontend against the experimental
                real_nepali profile using the same eSpeak NG vocoder.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <ModeButtons mode={mode} setMode={setMode} />
            <Button variant="outline" onClick={exportTsv}>
              <ArrowDownToLine className="h-4 w-4" />
              Export TSV
            </Button>
            <div className="rounded-md border px-3 py-2 text-sm text-muted-foreground">
              {completed}/{items.length} reviewed
            </div>
          </div>
        </header>

        <section className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="space-y-3">
            <Card>
              <CardContent className="space-y-3 p-4">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search words, focus, phones"
                    className="pl-9"
                  />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {(["all", "changed", "pending"] as const).map((value) => (
                    <Button
                      key={value}
                      variant={filter === value ? "default" : "outline"}
                      size="sm"
                      onClick={() => setFilter(value)}
                    >
                      {value}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="max-h-[calc(100svh-220px)] space-y-2 overflow-auto pr-1">
              {filtered.map((item) => {
                const state = reviewState[item.id]
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelectedId(item.id)}
                    className={cn(
                      "w-full rounded-lg border bg-background p-3 text-left transition-colors hover:bg-accent",
                      selected.id === item.id && "border-foreground",
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-lg font-semibold">{item.text}</span>
                      {state?.vote ? (
                        <Check className="h-4 w-4 text-foreground" />
                      ) : (
                        <span className="h-2 w-2 rounded-full bg-muted-foreground/40" />
                      )}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      <Badge variant={item.changed ? "default" : "muted"}>
                        {item.changed ? "changed" : "same"}
                      </Badge>
                      <Badge variant="outline">{item.focus}</Badge>
                    </div>
                  </button>
                )
              })}
            </div>
          </aside>

          <section className="space-y-5">
            <section className="space-y-4 rounded-lg border bg-background p-4 sm:p-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-4xl font-semibold tracking-normal">
                      {selected.text}
                    </h2>
                    <Badge variant="outline">{selected.focus}</Badge>
                  </div>
                  <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                    {selected.why}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="icon" onClick={() => move(-1)}>
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" onClick={() => move(1)}>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="grid gap-4 xl:grid-cols-2">
                <VoicePanel
                  title="Existing G2P"
                  description="Original frontend profile"
                  side={selected.old}
                  highlighted={activeState.vote === "old"}
                />
                <VoicePanel
                  title="real_nepali"
                  description="Experimental clear-profile output"
                  side={selected.real}
                  highlighted={activeState.vote === "real"}
                />
              </div>
            </section>

            <Card>
              <CardHeader>
                <CardTitle>Reviewer decision</CardTitle>
                <CardDescription>
                  Pick the voice a clear mainstream Nepali TTS should use for
                  this word.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2 sm:grid-cols-4">
                  <DecisionButton
                    active={activeState.vote === "old"}
                    onClick={() => updateVote(selected.id, "old")}
                  >
                    Existing
                  </DecisionButton>
                  <DecisionButton
                    active={activeState.vote === "real"}
                    onClick={() => updateVote(selected.id, "real")}
                  >
                    real_nepali
                  </DecisionButton>
                  <DecisionButton
                    active={activeState.vote === "tie"}
                    onClick={() => updateVote(selected.id, "tie")}
                  >
                    Tie
                  </DecisionButton>
                  <DecisionButton
                    active={activeState.vote === "bad"}
                    onClick={() => updateVote(selected.id, "bad")}
                  >
                    Bad sample
                  </DecisionButton>
                </div>
                <Textarea
                  value={activeState.notes}
                  onChange={(event) => updateNotes(selected.id, event.target.value)}
                  placeholder="Notes from native review, preferred phones, or why the sample is bad."
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Baseline limits</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm leading-6 text-muted-foreground md:grid-cols-3">
                <p>
                  Both samples use eSpeak NG&apos;s vocoder. This isolates G2P
                  differences, but it does not measure final neural TTS quality.
                </p>
                <p>
                  If both samples sound wrong, mark Bad sample and write the
                  target phones. The profile should change before training.
                </p>
                <p>
                  Do not train from a mixed manifest. The chosen profile must
                  rephonemize the whole training set first.
                </p>
              </CardContent>
            </Card>
          </section>
        </section>
      </div>
    </main>
  )
}

function ModeButtons({
  mode,
  setMode,
}: {
  mode: "frontend" | "audio"
  setMode: (mode: "frontend" | "audio") => void
}) {
  return (
    <div className="flex rounded-md border p-1">
      <Button
        variant={mode === "frontend" ? "default" : "ghost"}
        size="sm"
        onClick={() => setMode("frontend")}
      >
        <FileText className="h-4 w-4" />
        Frontend
      </Button>
      <Button
        variant={mode === "audio" ? "default" : "ghost"}
        size="sm"
        onClick={() => setMode("audio")}
      >
        <ListChecks className="h-4 w-4" />
        Listening
      </Button>
    </div>
  )
}

function FrontendAudit({
  data,
  mode,
  setMode,
}: {
  data: FrontendData
  mode: "frontend" | "audio"
  setMode: (mode: "frontend" | "audio") => void
}) {
  const [selectedId, setSelectedId] = useState(data.items[0]?.id ?? "")
  const [query, setQuery] = useState("")
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return data.items
    return data.items.filter((item) =>
      [
        item.id,
        item.category,
        item.input,
        item.normalizedText,
        item.phoneSequence.join(" "),
      ]
        .join(" ")
        .toLowerCase()
        .includes(q),
    )
  }, [data.items, query])
  const selected = filtered.find((item) => item.id === selectedId) ?? filtered[0]

  return (
    <main className="min-h-svh bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Text frontend</Badge>
              <Badge variant="muted">{data.items.length} cases</Badge>
              <Badge variant="muted">{data.profile}</Badge>
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-normal sm:text-3xl">
                Nepali text frontend audit
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                Inspect normalization, code-mixed spans, punctuation tokens,
                and generated phone sequences before training.
              </p>
            </div>
          </div>
          <ModeButtons mode={mode} setMode={setMode} />
        </header>

        <section className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="space-y-3">
            <Card>
              <CardContent className="space-y-3 p-4">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search cases, text, phones"
                    className="pl-9"
                  />
                </div>
              </CardContent>
            </Card>

            <div className="max-h-[calc(100svh-190px)] space-y-2 overflow-auto pr-1">
              {filtered.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedId(item.id)}
                  className={cn(
                    "w-full rounded-lg border bg-background p-3 text-left transition-colors hover:bg-accent",
                    selected?.id === item.id && "border-foreground",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-sm font-semibold leading-5">
                      {item.input}
                    </span>
                    {item.warnings.length ? (
                      <Badge className="border-transparent bg-destructive text-destructive-foreground">
                        {item.warnings.length}
                      </Badge>
                    ) : (
                      <Check className="mt-0.5 h-4 w-4 text-foreground" />
                    )}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    <Badge variant="outline">{item.category}</Badge>
                    <Badge variant="muted">{item.phoneSequence.length} phones</Badge>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          {selected ? <FrontendDetail item={selected} /> : null}
        </section>
      </div>
    </main>
  )
}

function FrontendDetail({ item }: { item: FrontendItem }) {
  return (
    <section className="space-y-5">
      <section className="space-y-4 rounded-lg border bg-background p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{item.category}</Badge>
          {item.warnings.length ? (
            <Badge className="border-transparent bg-destructive text-destructive-foreground">
              {item.warnings.length} warnings
            </Badge>
          ) : (
            <Badge variant="muted">clean</Badge>
          )}
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <TextBlock title="Input" text={item.input} />
          <TextBlock title="Normalized" text={item.normalizedText} />
        </div>
        <PhoneChips title="Phone sequence" phones={item.phoneSequence} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,0.7fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Tokens</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {item.tokens.map((token) => (
              <div
                key={token.id}
                className="grid gap-3 rounded-md border p-3 text-sm md:grid-cols-[minmax(0,1fr)_160px_minmax(0,1.4fr)]"
              >
                <div>
                  <div className="font-semibold">{token.raw}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {token.kind} · {token.language} · {token.source}
                  </div>
                </div>
                <Badge
                  variant={token.status === "review" ? "outline" : "muted"}
                  className="h-fit w-fit"
                >
                  {token.confidence || token.status}
                </Badge>
                <div className="flex flex-wrap gap-1">
                  {token.phones.map((phone, index) => (
                    <span
                      key={`${token.id}-${phone}-${index}`}
                      className="rounded border bg-muted/30 px-2 py-1 font-mono text-xs"
                    >
                      {phone}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-5">
          <Card>
            <CardHeader>
              <CardTitle>Chunks</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {item.chunks.map((chunk) => (
                <div key={chunk.id} className="rounded-md border p-3">
                  <div className="font-medium">{chunk.text}</div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    <Badge variant="outline">{chunk.boundary_strength}</Badge>
                    <Badge variant="muted">{chunk.sentence_type}</Badge>
                    <Badge variant="muted">{chunk.intonation_hint}</Badge>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Warnings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {item.warnings.length ? (
                item.warnings.map((warning, index) => (
                  <div key={index} className="rounded-md border p-3 text-sm">
                    <div className="font-medium">{warning.code}</div>
                    <div className="mt-1 text-muted-foreground">{warning.span}</div>
                  </div>
                ))
              ) : (
                <div className="rounded-md border p-3 text-sm text-muted-foreground">
                  No warnings.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>
    </section>
  )
}

function TextBlock({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <div className="mb-2 text-xs font-medium uppercase tracking-normal text-muted-foreground">
        {title}
      </div>
      <div className="min-h-20 rounded-md border bg-muted/30 p-3 text-lg leading-8">
        {text}
      </div>
    </div>
  )
}

function PhoneChips({ title, phones }: { title: string; phones: string[] }) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-normal text-muted-foreground">
        <Split className="h-3.5 w-3.5" />
        {title}
      </div>
      <div className="flex min-h-12 flex-wrap gap-1.5 rounded-md border bg-muted/30 p-3">
        {phones.map((phone, index) => (
          <span
            key={`${phone}-${index}`}
            className={cn(
              "rounded border bg-background px-2 py-1 font-mono text-xs",
              phone === "." && "text-muted-foreground",
            )}
          >
            {phone}
          </span>
        ))}
      </div>
    </div>
  )
}

function DecisionButton({
  active,
  children,
  onClick,
}: {
  active: boolean
  children: React.ReactNode
  onClick: () => void
}) {
  return (
    <Button
      variant={active ? "default" : "outline"}
      className="justify-start"
      onClick={onClick}
    >
      {active ? <Check className="h-4 w-4" /> : <CircleSlash className="h-4 w-4" />}
      {children}
    </Button>
  )
}

function VoicePanel({
  title,
  description,
  side,
  highlighted,
}: {
  title: string
  description: string
  side: VoiceSide
  highlighted: boolean
}) {
  return (
    <Card className={cn("overflow-hidden", highlighted && "border-foreground")}>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <Badge variant="outline">{side.source}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <audio className="h-10 w-full" controls preload="none" src={side.audio} />
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-normal text-muted-foreground">
            <Split className="h-3.5 w-3.5" />
            Phones
          </div>
          <div className="flex min-h-12 flex-wrap gap-1.5 rounded-md border bg-muted/30 p-3">
            {side.phones.map((phone, index) => (
              <span
                key={`${phone}-${index}`}
                className={cn(
                  "rounded border bg-background px-2 py-1 font-mono text-xs",
                  phone === "." && "text-muted-foreground",
                )}
              >
                {phone}
              </span>
            ))}
          </div>
        </div>
        <div>
          <div className="mb-2 text-xs font-medium uppercase tracking-normal text-muted-foreground">
            eSpeak payload
          </div>
          <code className="block max-h-24 overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs leading-5">
            {side.espeakPayload}
          </code>
        </div>
      </CardContent>
    </Card>
  )
}

export default App
