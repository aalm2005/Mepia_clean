// Los recorridos de regresión cierran la introducción mediante su control real.
async function dismissTutorialWhenPresent(page) {
  await page.addLocatorHandler(
    page.getByRole("dialog", {name: "Tutorial de MEPIA", exact: true}),
    async () => { await page.getByRole("button", {name: "Cerrar tutorial", exact: true}).click(); }
  );
}
module.exports = {dismissTutorialWhenPresent};
