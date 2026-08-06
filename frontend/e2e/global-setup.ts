async function globalSetup() {
  try {
    const res = await fetch('http://localhost:9090/health');
    if (!res.ok) throw new Error(`status ${res.status}`);
  } catch (err) {
    throw new Error(
      'Backend is not reachable at http://localhost:9090/health. ' +
      'Start the backend (uvicorn main:app --port 9090) before running e2e tests. ' +
      `Original error: ${err}`
    );
  }
}

export default globalSetup;
