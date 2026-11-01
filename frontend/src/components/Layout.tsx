import { Link, NavLink, Outlet } from "react-router";

import { formatDate } from "../lib/format";
import { useMeta } from "../lib/useMeta";
import { text } from "../text/pt-BR";
import styles from "./Layout.module.css";

export function Layout() {
  const meta = useMeta();
  return (
    <div className={styles.layout}>
      <header>
        <nav className={styles.nav} aria-label="Principal">
          <Link to="/" className={styles.brand}>
            {text.appName}
          </Link>
          <NavLink to="/">{text.nav.officials}</NavLink>
          <NavLink to="/comparar">{text.nav.compare}</NavLink>
          <NavLink to="/partidos">{text.nav.parties}</NavLink>
          <NavLink to="/metodologia">{text.nav.methodology}</NavLink>
        </nav>
        <p className={styles.snapshot} role="status">
          {meta.data?.snapshot_date ? text.snapshot(formatDate(meta.data.snapshot_date)) : meta.isLoading ? text.loading : text.noSnapshot}
        </p>
      </header>
      <Outlet />
      <footer className={styles.footer}>{text.tagline}</footer>
    </div>
  );
}
