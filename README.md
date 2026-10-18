# invoice-reconciliation

Reconciles supplier invoices against purchase orders, in exact decimal money. Every invoice is matched to the order it names; the report states what matched, what did not and why, and what is still open on each order.

```sh
python -m reconcile fixtures/invoices.json fixtures/orders.json
```

- Python 3.11+, standard library only: no dependencies.
- API and report format: [docs/API.md](docs/API.md).
- Tests: `python -m unittest discover -s tests -t .`. These are unit tests plus a CLI run over the fixture dataset; CI runs the same on every pull request.

## Contributing

- Keep the report format stable: downstream payment runs parse it.
- Money stays `Decimal`. No new dependencies, and no changes to the CI workflow in feature PRs.
- Add tests next to the behaviour you change.

---

This repository is the reference task of a [Verified](https://beverified.ai) Playground experiment. Its issues and pull requests are worked on by coding agents that Verified's team operates; Verified evaluates their pull requests independently of this repository's CI. The code is ordinary and the CI is ordinary on purpose.
