import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";

import { Layout } from "./components/Layout";
import { ComparePage } from "./pages/ComparePage";
import { MethodologyPage } from "./pages/MethodologyPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { OfficialPage } from "./pages/OfficialPage";
import { OfficialsPage } from "./pages/OfficialsPage";
import { PartiesPage } from "./pages/PartiesPage";

export function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { staleTime: 5 * 60 * 1000, retry: 1 } } });
}

const queryClient = makeQueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<OfficialsPage />} />
        <Route path="/parlamentar/:id" element={<OfficialPage />} />
        <Route path="/comparar" element={<ComparePage />} />
        <Route path="/partidos" element={<PartiesPage />} />
        <Route path="/metodologia" element={<MethodologyPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
