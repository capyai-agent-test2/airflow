## React plugin template rules

- Keep changes small and local to the plugin.
- Use TypeScript types instead of `any`.
- Prefer updating existing components over adding new abstraction layers.
- Keep React, React DOM, and shared UI dependencies compatible with the host application.
- Treat the plugin as a library: exported component APIs should stay simple and stable.
- Favor accessible UI patterns and sensible empty, loading, and error states.
- When adding dependencies, justify them and prefer the existing stack first.
- Keep build configuration changes narrow; avoid changing external dependency handling unless required.
- Add or update focused tests for new behavior.
