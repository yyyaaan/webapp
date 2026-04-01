Private note:

Open project in the dev container where `opencode` is available in the container.

```
# this installation is not auotmated
udo chown -R $(whoami) .sisyphus
npx oh-my-opencode install

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend: Vaporwave from designprompts.dev