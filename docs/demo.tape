# vhs tape for docs/demo.gif — run `vhs docs/demo.tape` from a checkout that has a
# profile/rubric and today's RADAR.md already produced by `/jobradar today`.
# The collect step is real (network); the grade step is shown as its result, because the
# grading happens inside Claude Code and recording that would spend tokens on every re-render.

Output docs/demo.gif

Set Shell "zsh"
Set FontSize 14
Set Width 1000
Set Height 640
Set Theme "Catppuccin Mocha"
Set TypingSpeed 30ms

Hide
Type "setopt interactive_comments; PS1='%F{green}jobradar%f $ '; clear"
Enter
Sleep 500ms
Show

Type "# /jobradar today — step 1 of 2: collect (runs here, no signup, no model calls)"
Enter
Sleep 800ms
Type "python -m radar.collect --only saramin,jumpit"
Enter
Sleep 9s

Type "clear"
Enter
Type "# step 2 of 2: Claude grades every posting against profile/rubric.md -> RADAR.md"
Enter
Sleep 800ms
Type "sed -n '1,26p' RADAR.md"
Enter
Sleep 7s
