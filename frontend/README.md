# Frontend structure

The UI is split by responsibility so that the app shell stays small and each part can change independently.

```text
src/
  App.vue                    page composition and active tab
  components/                map, playback controls, gauges, charts, data and formula views
  composables/                trip loading, playback state and chart calculations
  services/api.ts             typed HTTP boundary to FastAPI
  types/domain.ts             shared API/domain types
  utils/                      number/time formatting and reusable series helpers
  styles/                     design tokens, shell, trip, data and responsive rules
  main.ts                     Vue bootstrap and global styles
```

## Data flow

`useTripData` loads the route, telemetry and dataset comparison through `services/api.ts`, then requests analysis for the loaded versions. `useTripPlayback` owns playback time and derives the current interpolated vehicle and route position. `App.vue` passes that state to the map and dashboard components. Chart series are prepared in `useRouteChart`; the chart component only renders axes, lines and the current-position cursor.

Keep HTTP response types in `types/domain.ts`, URL/fetch details in `services/api.ts`, and avoid moving feature-specific state into `App.vue`. Add UI behavior in the relevant component or composable.
