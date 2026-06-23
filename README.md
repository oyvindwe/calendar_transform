# Calendar Transform

A Home Assistant helper integration that wraps an existing calendar entity and transforms its events using regular expressions matched against each event's `description`. It can:

- **Rewrite summaries** — replace each event's `summary` with text extracted from its description.
- **Filter events** — hide events whose description matches a pattern.

You can use either capability on its own, or both together. It's useful when you display a public or read-only calendar that you can't edit at the source: when the text you want to render is buried in the description, or when the feed contains entries you'd rather not see.

[![BuyMeCoffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/oyvindwev)

## Rewriting summaries

A football match calendar provides events like:

Summary:
```text
Jenter 08 år avd. 02
```

Description:
```text
 Jenter 08 år avd. 02 (runde 3)

 Dikemark J8 Sparkles - Jutul J8 Grønn
 Dikemark kunstgress 5er A torsdag 01.05.25 18.00 

 www.fotball.no
```

Configuring the integration with the regex `\n\n\s(.*)\n` (and an empty replacement) makes the wrapped calendar expose:

```text
summary: "Dikemark J8 Sparkles - Jutul J8 Grønn"
```

For more elaborate cases, you can use multiple capture groups together with a replacement template. For example, the pattern `\n\n\s(.+) - (.+)\n` with replacement `\2 vs \1` produces:

```text
summary: "Jutul J8 Grønn vs Dikemark J8 Sparkles"
```

All other event fields (start, end, location, etc.) pass through unchanged.

## Filtering events

Some calendars contain entries you never want to see. A common case: Google Calendar can inject **Google Tasks** as synthetic events when "Show tasks in Calendar" is enabled. Their titles are unpredictable, so a title-based filter can't reliably catch them — but every such event carries `tasks.google.com/task/` in its description.

The optional **Filter pattern** is a Python regex (applied with `re.MULTILINE`) matched against each event's description. Any event whose description matches is hidden from the wrapped calendar, while real calendar events are left alone.

For example, to hide Google Tasks:

```text
filter: tasks\.google\.com/task/
```

This lets you keep "Show tasks in Calendar" enabled in Google Calendar while still excluding the tasks from a dashboard or card that reads the wrapped calendar — without having to turn task visibility off entirely.

The same approach works for any source that injects events carrying consistent text in their description, for example:

```text
# hide events forwarded from a particular integration
filter: Sent from My Other App

# hide more than one marker at once (regex alternation)
filter: tasks\.google\.com/task/|holiday in
```

Notes:

- The filter is independent of the summary rewrite — you can use either, both, or neither. Filtered events are removed before any summary rewriting happens.
- Unlike the substitute pattern, the filter pattern does **not** need a capture group; it only has to match.
- Events with no description are never filtered.
- Leave the field empty to keep all events.

## Installation

You can install using HACS or download.

### HACS

If you have [HACS](https://hacs.xyz/) installed, add this repository (`oyvindwe/calendar_transform`) as a custom repository of type "Integration."

See https://hacs.xyz/docs/faq/custom_repositories/

### Download

Download the `custom_components/calendar_transform/` directory and place it in your `<config>/custom_components/`.

After installing, you need to restart Home Assistant.

## Configuration

Add via **Settings → Devices & services → Add integration → Calendar Transform**:

- **Name** — the entity name for the new wrapped calendar
- **Source calendar** — the calendar whose events will be transformed
- **Substitute pattern** — Python regex with at least one capture group, applied with `re.MULTILINE`. The summary is replaced with text from the match; if a given event's description doesn't match, the original summary is kept. Leave empty to only filter events.
- **Replacement** — template used to build the new summary, with backreferences like `\1`, `\2` referring to the substitute pattern's capture groups. Leave empty to use the first capture group.
- **Filter pattern** — optional Python regex, applied with `re.MULTILINE`. Events whose description matches are hidden from the wrapped calendar. Leave empty to keep all events. For example, `tasks\.google\.com/task/` hides Google Tasks that Google Calendar injects as events.

At least one of the **Substitute pattern** or **Filter pattern** must be provided.

## Behavior

- The wrapper does not cache events — `async_get_events()` is forwarded to the source for every query.
- The source calendar is never modified; events are copied with `dataclasses.replace` before transformation.
- If the source entity becomes unavailable, the wrapped calendar reports unavailable too.
