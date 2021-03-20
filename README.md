# language-benchmarks
Benchmarks of various programming languages

## Benchmarking

Run the benchmarks with

```sh
./bench.sh
```

### Go Board

A benchmark that requires reading Go moves from stdin, playing them on a Go board and printing the final score.

Moves are provided in [GTP](https://www.lysator.liu.se/~gunnar/gtp/), the Go Text Protocol. Final scoring uses [Tromp-Taylor](https://senseis.xmp.net/?TrompTaylorRules).

## Development

Run tests for all languages with

```sh
./test.sh
```