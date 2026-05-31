# Calendar Transform

A Home Assistant helper integration that wraps an existing calendar entity and rewrites each event's `summary` using a regular expression matched against the event's `description`.

Useful when you display a public, read-only calendar whose summaries are not the text you want to render — but the desired text is buried inside the description.

## Example

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
- **Regex pattern** — Python regex with at least one capture group, applied with `re.MULTILINE`. If a given event's description doesn't match, the original summary is kept.
- **Replacement** — template used to build the new summary, with backreferences like `\1`, `\2` referring to the regex's capture groups. Leave empty to use the first capture group.

## Behavior

- The wrapper does not cache events — `async_get_events()` is forwarded to the source for every query.
- The source calendar is never modified; events are copied with `dataclasses.replace` before transformation.
- If the source entity becomes unavailable, the wrapped calendar reports unavailable too.
