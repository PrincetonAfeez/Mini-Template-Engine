# Template Grammar (V1)

Informal EBNF for the mini template engine syntax.

## Template

```ebnf
template     = { element } ;
element      = text | variable | block | comment ;
text         = { any char except unescaped "{{", "{%", "{#" } ;
variable     = "{{" ws expr ws "}}" ;
block        = "{%" ws block_body ws "%}" ;
comment      = "{#" ws { any } ws "#}" ;
```

Whitespace trim markers: `{{-`, `-}}`, `{%-`, `-%}` strip adjacent whitespace.

## Blocks

```ebnf
block_body   = if_block | elif_block | else_block | endif
               | for_block | endfor
               | set_block
               | "raw" ;
if_block     = "if" ws condition ;
elif_block   = "elif" ws condition ;
else_block   = "else" ;
endif        = "endif" ;
for_block    = "for" ws name ws "in" ws expr ;
endfor       = "endfor" ;
set_block    = "set" ws name ws "=" ws expr ;
```

Raw blocks: `{% raw %} ... {% endraw %}` (case-insensitive `endraw`).

## Expressions

```ebnf
expr         = value { "|" ws filter } ;
value        = literal | path ;
path         = segment { "." segment } ;
segment      = identifier | integer ;
filter       = name [ "(" arg { "," arg } ")" ] ;
literal      = bool | null | number | string ;
bool         = "true" | "false" ;
null         = "none" | "null" ;
```

## Conditions

```ebnf
condition    = [ "not" ws ] value
               | value ws ("==" | "!=") ws value ;
```

Only one comparison operator per condition. No `and` / `or`.

## Identifiers

```ebnf
identifier   = ( letter | "_" ) { letter | digit | "_" } ;
```

Names starting with `_` are forbidden in templates.
