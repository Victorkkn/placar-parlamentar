import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "../api/client";

export function useMeta() {
  return useQuery({ queryKey: ["meta"], queryFn: () => unwrap(api.GET("/api/meta")) });
}
