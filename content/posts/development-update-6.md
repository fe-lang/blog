+++
title = "Fe Development Update #6"
date = "2021-05-31"
+++


It's been a month since our [last update](/posts/fe-development-update-5/). In this time, we've merged a total of 22 pull requests from 4 different contributors. Here are some highlights.

## We shipped v0.5.0-alpha "Evenkite"

This release contains much of the work we'll cover in this update. You can head over to [the release page](https://github.com/ethereum/fe/releases/tag/v0.5.0-alpha) for more info and downloads.

## Generic arguments (partially implemented)

We've added generic arguments syntax to type descriptions and expressions. This cleans up some existing sore spots in our syntax and prepares us for full-on generic support.

Previously, map type arguments (e.g. `map<u256, address>`) were handled as a special case in the parser. We were also using an ugly syntax for *strings* (e.g. `string42`), where the numeric suffix indicated the maximum size of the string. We've now updated the parser to handle generic arguments on all types, so maps are no longer a special case and the max size of strings are expressed using the same syntax as maps (e.g. `String<42>`). In the case of strings, the generic argument is a *const* value rather than a type.

For now, these are just syntax changes and the underlying type implementations remain the same. In the future, though, we'll be adding support for generic arguments in type definitions. This will enable us to pull the definitions of strings, maps, and other types out of the compiler and into libraries. This will improve the composability of Fe and establish patterns that other developers can use to implement their own types.

**Relevant PRs:**
- *Remove `ast::TypeDesc::Map` in favor of `TypeDesc::Generic` [#384](https://github.com/ethereum/fe/pull/384)*
- *Allow generic arguments in `Expr::Call` [#425](https://github.com/ethereum/fe/pull/425)*

## More expressions

[Y-Nak](https://github.com/Y-Nak) added support for a few more numeric representations. You can now choose between hexadecimal, decimal, octal, or binary when writing numbers. Feel free to pick whichever one makes your code most readable!

```
value_hex: u256 = 0xff
value_octal: u256 = 0o77
value_binary: u256 = 0b11
```

We've also added support for list expressions.

```
my_array: u256[4] = [1, 2, 3, 4]
```

**Relevant PRs:**
- *Allow hex/octal/binary radix numeric literals [#410](https://github.com/ethereum/fe/pull/410)*
- *Lower list expressions [#388](https://github.com/ethereum/fe/pull/388)*

## Developer on-boarding

We're getting to a point where Fe is reliable and feature-rich enough for developers to start using it. With this being the case, we need to make the language and its tools more accessible. This means we need to have development resources written and made easily available. To this end, [cburgdorf](https://github.com/cburgdorf/) has been working on improving the website and resources that it links to.

**Relevant PRs:**
- *Fill in Quickstart in Fe guide [#403](https://github.com/ethereum/fe/pull/403)*
- *Bring minimal viable website to life [#394](https://github.com/ethereum/fe/pull/394)*

## Other features and bugfixes

- *Dynamically sized return support for external calls [#415](https://github.com/ethereum/fe/pull/415)*
- *Validate that tuple attributes are prefixed with 'item' [#401](https://github.com/ethereum/fe/pull/401)*
- *Added a unit type [#406](https://github.com/ethereum/fe/pull/406)*
- *AST cleanup [#395](https://github.com/ethereum/fe/pull/395)*
- *Panic if context.add_ methods are called twice [#392](https://github.com/ethereum/fe/pull/392)*
- *Approval testing for the Analyzer [#387](https://github.com/ethereum/fe/pull/387)*
- *Restrict var decl target to name or tuple [#386](https://github.com/ethereum/fe/pull/386)*
- *Speed up building and running of tests [#383](https://github.com/ethereum/fe/pull/383)*

## What's next

Our goal of shipping a non-alpha release this year still stands. Over the next few months, we will continue hardening the compiler, improving documentation, and polishing off existing features.

---

Stay tuned for more monthly updates and releases.



