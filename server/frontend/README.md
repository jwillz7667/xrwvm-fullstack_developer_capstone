# OpenRoad React interface

This frontend uses React and Vite. Run the complete application with the root `compose.yaml`; Django serves the production bundle and same-origin API.

```sh
npm ci
npm run lint
npm run build
```

The build writes `dist/`. Django collects the generated assets into its static directory. See the root README for initialization, service architecture, and authentication.
