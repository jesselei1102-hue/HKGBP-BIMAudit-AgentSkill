// Window buttons that post to the chat: a second click while the first is still sending does nothing.

/** Wraps an async action so a call made while the previous one is running is ignored. */
export function singleFlight<A extends unknown[]>(fn: (...args: A) => Promise<void>): (...args: A) => Promise<void> {
  let running = false;
  return async (...args: A) => {
    if (running) return;
    running = true;
    try {
      await fn(...args);
    } finally {
      running = false;
    }
  };
}
