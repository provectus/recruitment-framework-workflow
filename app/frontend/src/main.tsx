import { useAuth } from "@/features/auth";
import { getMeApiAuthMeGetQueryKey } from "@/shared/api/@tanstack/react-query.gen";
import { client } from "@/shared/api/client.gen";
import { QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { AxiosError } from "axios";
import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { routeTree } from "./routeTree.gen";

client.setConfig({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
});

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      if (error instanceof AxiosError && error.response?.status === 401) {
        queryClient.setQueryData(getMeApiAuthMeGetQueryKey(), null as never);
      }
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: (failureCount, error) => {
        if (error instanceof AxiosError && error.response?.status === 401) return false;
        return failureCount < 1;
      },
    },
  },
});

const router = createRouter({
  routeTree,
  context: { auth: undefined! },
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function InnerApp() {
  const auth = useAuth();
  if (auth.isLoading) return null;
  return <RouterProvider router={router} context={{ auth }} />;
}

const rootElement = document.getElementById("root")!;
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <InnerApp />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </StrictMode>,
  );
}
