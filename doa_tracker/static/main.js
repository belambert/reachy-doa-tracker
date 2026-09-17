const status = document.getElementById("status");
const radios = document.querySelectorAll('input[name="mode"]');

async function request(method, body) {
    try {
        const resp = await fetch("/mode", {
            method,
            headers: { "Content-Type": "application/json" },
            body: body && JSON.stringify(body),
        });
        showMode((await resp.json()).mode);
    } catch (e) {
        status.textContent = "Backend error";
    }
}

function showMode(mode) {
    radios.forEach((r) => (r.checked = r.value === mode));
    status.textContent = `Tracking with: ${mode}`;
}

radios.forEach((r) =>
    r.addEventListener("change", () => request("POST", { mode: r.value }))
);

request("GET");
