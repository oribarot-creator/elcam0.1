import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [games, setGames] = useState([]);
  const [name, setName] = useState('');
  const [path, setPath] = useState('');
  const [isLoadingGames, setIsLoadingGames] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [runningGameId, setRunningGameId] = useState(null);
  const [removingGameId, setRemovingGameId] = useState(null);
  const [status, setStatus] = useState(null);

  const fetchGames = async () => {
    setIsLoadingGames(true);
    try {
      const { data } = await axios.get('/api/games');
      setGames(data);
    } catch (error) {
      setStatus({
        type: 'error',
        text: 'Could not load your game library. Please refresh and try again.',
      });
    } finally {
      setIsLoadingGames(false);
    }
  };

  useEffect(() => { fetchGames(); }, []);

  const addGame = async e => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatus(null);
    try {
      await axios.post('/api/games', { name: name.trim(), path: path.trim() });
      setName('');
      setPath('');
      await fetchGames();
      setStatus({ type: 'success', text: 'Game added to your library.' });
    } catch (error) {
      setStatus({
        type: 'error',
        text: 'Could not add the game. Check the file path and try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const runGame = async id => {
    setRunningGameId(id);
    setStatus(null);
    try {
      await axios.post(`/api/games/${id}/run`);
      setStatus({ type: 'success', text: 'Game launched. Check your terminal window.' });
    } catch (error) {
      setStatus({ type: 'error', text: 'Game launch failed. Verify the game path first.' });
    } finally {
      setRunningGameId(null);
    }
  };

  const removeGame = async id => {
    setRemovingGameId(id);
    setStatus(null);
    try {
      await axios.delete(`/api/games/${id}`);
      await fetchGames();
      setStatus({ type: 'success', text: 'Game removed from your library.' });
    } catch (error) {
      setStatus({ type: 'error', text: 'Could not remove game. Please try again.' });
    } finally {
      setRemovingGameId(null);
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-8 sm:py-12">
      <section className="fade-in rounded-3xl border border-white/60 bg-white/75 p-6 shadow-card backdrop-blur-sm sm:p-8">
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.22em] text-ember-700">Launcher Console</p>
        <h1 className="text-3xl font-bold leading-tight text-slate-900 sm:text-4xl">
          My Python Games Library
        </h1>
        <p className="mt-3 max-w-2xl text-sm text-slate-600 sm:text-base">
          Keep your scripts in one place and launch them instantly with clear run feedback.
        </p>
      </section>

      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <article className="slide-up rounded-3xl border border-slate-200 bg-white p-6 shadow-card">
          <h2 className="text-xl font-semibold text-slate-900">Add a game</h2>
          <p className="mt-1 text-sm text-slate-600">Include a display name and the script filename.</p>

          <form className="mt-5 space-y-4" onSubmit={addGame}>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="game-name">
                Game name
              </label>
              <input
                id="game-name"
                className="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-ember-500 focus:bg-white focus:ring-4 focus:ring-ember-100"
                placeholder="Example: Number Guess"
                value={name}
                onChange={e => setName(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="game-path">
                Script filename
              </label>
              <input
                id="game-path"
                className="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-100"
                placeholder="Example: guess.py"
                value={path}
                onChange={e => setPath(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-xl bg-slate-900 px-4 py-3 font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? 'Saving...' : 'Add game to library'}
            </button>
          </form>
        </article>

        <article className="slide-up rounded-3xl border border-slate-200 bg-white p-6 shadow-card" style={{ animationDelay: '90ms' }}>
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-slate-900">Games in library</h2>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {games.length} total
            </span>
          </div>

          {isLoadingGames && (
            <p className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              Loading your games...
            </p>
          )}

          {!isLoadingGames && games.length === 0 && (
            <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center text-sm text-slate-600">
              Your library is empty. Add your first game from the form.
            </p>
          )}

          {!isLoadingGames && games.length > 0 && (
            <ul className="space-y-3" aria-live="polite">
              {games.map((g, index) => (
                <li
                  key={g.id}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-4 transition hover:border-slate-300 hover:bg-white"
                  style={{ animationDelay: `${120 + index * 70}ms` }}
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{g.name}</p>
                      <p className="text-sm text-slate-600">{g.path}</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => runGame(g.id)}
                        disabled={runningGameId === g.id || removingGameId === g.id}
                        className="rounded-lg bg-ember-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-ember-700 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {runningGameId === g.id ? 'Launching...' : 'Run game'}
                      </button>
                      <button
                        onClick={() => removeGame(g.id)}
                        disabled={removingGameId === g.id || runningGameId === g.id}
                        className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {removingGameId === g.id ? 'Removing...' : 'Remove'}
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      {status && (
        <section
          aria-live="assertive"
          className={`mt-6 rounded-xl px-4 py-3 text-sm font-medium ${
            status.type === 'success'
              ? 'border border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border border-rose-200 bg-rose-50 text-rose-800'
          }`}
        >
          {status.text}
        </section>
      )}
    </main>
  );
}

export default App;