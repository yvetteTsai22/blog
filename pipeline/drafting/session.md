## How this session works (spec §1.6)

You are Yvette's drafting partner in the `draft-blog` worktree. Nothing happens until she picks.
Do not push anything, ever: `draft-blog` stays local. Do not stash. Do not switch branches.
Read literature-note bodies through Notion MCP only after a pick.

### After Yvette picks a topic

If Yvette says the topic already has a draft or published article, treat that as a pick to
repair the records: do not start a second draft. Confirm the existing article's path and slug,
then link the literature notes to its permanent note and set the statuses to match the actual
state. If the match is ambiguous, ask before changing records.

1. **Mark the pick.** Through Notion MCP, set `pick_status=挑中` on every literature note of
   that topic (all notes sharing its `topic_of`). Then run `git merge master` once in this
   worktree. If the merge conflicts, stop and tell her; do not resolve it yourself.
2. **Permanent note first.** Create one Slip box page: `note type=permanant note`,
   `status=Reviewed`, `blog status=寫作中`. Write with her: what this means, and which old
   Slip box notes are the same idea. Link the topic's literature notes and those old notes with
   `Parent item`.
   For an existing draft, reuse its `draft path` and `slug`; for a published article, set
   `blog status=已發表` and use its frozen `slug` instead of creating another draft.
   If she wants to skip the note, still create it, empty, with `blog status=寫作中` and
   `note pending=true`.
3. **Draft.** Agree a slug (kebab-case, at most 6 words). Grow the draft from the note into
   `_drafts/<slug>.md`, using the blog `CLAUDE.md`, the `article-writing` skill and the two
   voice samples above. Front matter follows §5.3 (see the publish checklist below). Leave
   the `date` key out of the draft entirely: an empty `date:` fails the whole Jekyll build.
   Images for the post go in `assets/img/<slug>/`.
4. **Before leaving: one commit for this one article.** `_drafts/` is gitignored, so stage it
   with force, and stage nothing else:

       git add -f _drafts/<slug>.md assets/img/<slug>
       git commit -m "📝doc: draft <slug>"

   One commit touches one article. Then update the permanent note: `blog status=寫作中`,
   `draft path=_drafts/<slug>.md`, `slug=<slug>`.
   Never commit before Yvette has seen the draft and said to commit it.

### Publish (only when Yvette says "publish")

Check the draft's front matter first. Every field below must be present and valid, or the
publish is blocked: say which fields are missing and stop.

- `layout: post`, `title`, `author: yvetteTsai`, `description` (at most 160 chars)
- `category`: one of `agents` / `debugging` / `patterns` / `guides` / `life` (empty blocks)
- `image` and `optimized_image`: the same Unsplash photo at `w=2670` and `w=800`; offer 2–3
  candidates and let her pick
- `date`: the publish time with the machine's current UTC offset (`date +%z`, e.g. `+0100`
  in London summer time); never hard-code an offset
- `slug`: kebab-case, at most 6 words, frozen after publish
- `tags`: 2–6, only from `_data/tags.yml`; a new tag needs her approval
- optional `subtitle`; omit `paginate` unless needed
- `--page-break--` only works with `paginate: true`: if the body has the marker, set
  `paginate: true`; otherwise remove the marker (it renders as plain text)

Then, step by step, with her confirmation before the push:

1. In the `master` checkout: `git checkout draft-blog -- _drafts/<slug>.md` (use this
   worktree's branch name). If the post has images, check out the whole `assets/img/<slug>/`
   too: `_config.yml` excludes `assets/img/*/*.html` and `*.json`, so diagram sources stay in
   the repo without being published.
2. Move it to `_posts/<YYYY-MM-DD>-<slug>.md`, add `date`, run
   `bundle exec jekyll build --baseurl '/blog' -d /tmp/blog-publish-check`, commit, and push
   `master` (that deploys).
3. Delete the draft and `assets/img/<slug>/` from `draft-blog` (`git rm`, then commit).
The 21:00 run marks the permanent note `已發表` once the post is on `master`.
