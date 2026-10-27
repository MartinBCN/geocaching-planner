import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useContext, useEffect, useRef, useState } from "react";
import { api, importApi } from "../../api/client";
import type { components } from "../../api/schema";
import { ImportActivityContext } from "../../app/ImportActivityContext";

type ImportRun = components["schemas"]["ImportRunResponse"];
type ImportIssue = components["schemas"]["ImportIssueResponse"];

const IMPORTS_KEY = ["imports"];

async function fetchImports(): Promise<ImportRun[]> {
  const { data, error } = await api.GET("/api/v1/imports");
  if (!data) {
    throw new Error(error?.detail ?? "Unable to load import history.");
  }
  return data;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function Counts({ run }: { run: ImportRun }) {
  return (
    <span>
      {run.created} created, {run.updated} updated, {run.unchanged} unchanged,{" "}
      {run.waypoints} waypoints
    </span>
  );
}

function IssueList({
  issues,
  severity,
}: {
  issues: ImportIssue[];
  severity: string;
}) {
  const filtered = issues.filter((issue) => issue.severity === severity);
  if (filtered.length === 0) {
    return null;
  }
  return (
    <section>
      <h3>{severity === "warning" ? "Warnings" : "Errors"}</h3>
      <ul>
        {filtered.map((issue) => (
          <li
            key={`${issue.severity}-${issue.file}-${issue.gc_code}-${issue.line}-${issue.code}-${issue.message}`}
          >
            <strong>{issue.file}</strong>
            {issue.gc_code ? ` · ${issue.gc_code}` : ""}
            {issue.line !== null ? ` · line ${issue.line}` : ""}
            {` · ${issue.message} (${issue.code})`}
          </li>
        ))}
      </ul>
    </section>
  );
}

function RunDetails({ run }: { run: ImportRun }) {
  return (
    <>
      <p>
        <strong>Files:</strong> {run.filenames.join(", ")}
      </p>
      <p>
        <strong>Imported:</strong>{" "}
        <time dateTime={run.started_at}>{formatDate(run.started_at)}</time>
      </p>
      <p>
        <strong>Summary:</strong> <Counts run={run} />
      </p>
      <IssueList issues={run.errors} severity="error" />
      <IssueList issues={run.errors} severity="warning" />
      {run.errors.length === 0 && <p>No errors or warnings.</p>}
    </>
  );
}

export function ImportPage() {
  const queryClient = useQueryClient();
  const activity = useContext(ImportActivityContext);
  const setIsImporting = activity?.setIsImporting;
  const fileInput = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [summary, setSummary] = useState<ImportRun | null>(null);
  const importsQuery = useQuery({
    queryKey: IMPORTS_KEY,
    queryFn: fetchImports,
  });
  const importMutation = useMutation({
    mutationFn: async (files: File[]) => {
      const { data, error } = await importApi.POST("/api/v1/imports", {
        body: { files },
        bodySerializer: (body) => {
          const form = new FormData();
          for (const file of body.files) {
            form.append("files", file, file.name);
          }
          return form;
        },
      });
      if (!data) {
        throw new Error(error?.detail ?? "The import failed.");
      }
      return data;
    },
    onSuccess: async (run) => {
      setSummary(run);
      setSelectedFiles([]);
      if (fileInput.current) {
        fileInput.current.value = "";
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["imports"] }),
        queryClient.invalidateQueries({ queryKey: ["caches"] }),
      ]);
    },
  });

  useEffect(() => {
    if (!setIsImporting) {
      return;
    }
    setIsImporting(importMutation.isPending);
    return () => setIsImporting(false);
  }, [setIsImporting, importMutation.isPending]);

  useEffect(() => {
    if (!importMutation.isPending) {
      return;
    }
    function warnBeforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", warnBeforeUnload);
    return () => window.removeEventListener("beforeunload", warnBeforeUnload);
  }, [importMutation.isPending]);

  function addFiles(files: FileList | File[]) {
    setSelectedFiles(Array.from(files));
    setSummary(null);
  }

  function onDrop(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    if (!importMutation.isPending) {
      addFiles(event.dataTransfer.files);
    }
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedFiles.length > 0) {
      importMutation.mutate(selectedFiles);
    }
  }

  if (!activity) {
    throw new Error("ImportPage must be rendered inside AppShell.");
  }

  return (
    <section className="import-page">
      <h1>Import Pocket Queries</h1>
      <p>Choose one or more .gpx or .zip Pocket Query files.</p>

      <form
        onSubmit={submit}
        onDragOver={(event) => event.preventDefault()}
        onDrop={onDrop}
      >
        <div className="import-dropzone">
          <p>Drag files here, or choose them from your computer.</p>
          <button
            type="button"
            disabled={importMutation.isPending}
            onClick={() => fileInput.current?.click()}
          >
            Choose files…
          </button>
          <input
            ref={fileInput}
            id="import-files"
            className="import-file-input"
            type="file"
            accept=".gpx,.zip"
            multiple
            aria-label="Choose files…"
            disabled={importMutation.isPending}
            onChange={(event) => addFiles(event.currentTarget.files ?? [])}
          />
        </div>

        {selectedFiles.length > 0 && (
          <ul aria-label="Selected files">
            {selectedFiles.map((file) => (
              <li key={`${file.name}-${file.size}-${file.lastModified}`}>
                {file.name}
              </li>
            ))}
          </ul>
        )}
        {importMutation.isPending && (
          <p role="status">
            Importing… {selectedFiles.map((file) => file.name).join(", ")}
          </p>
        )}
        {importMutation.isError && (
          <p role="alert">{importMutation.error.message}</p>
        )}
        <button
          type="submit"
          disabled={importMutation.isPending || selectedFiles.length === 0}
        >
          Import files
        </button>
      </form>

      {summary && (
        <section
          className="import-summary"
          aria-labelledby="import-summary-heading"
        >
          <h2 id="import-summary-heading">Import summary</h2>
          <RunDetails run={summary} />
        </section>
      )}

      <section
        className="import-history"
        aria-labelledby="import-history-heading"
      >
        <h2 id="import-history-heading">Import history</h2>
        {importsQuery.isPending && <p role="status">Loading import history…</p>}
        {importsQuery.isError && (
          <p role="alert">{importsQuery.error.message}</p>
        )}
        {importsQuery.data?.length === 0 && (
          <p>
            No imports yet. Choose Pocket Query files to start your cache
            library.
          </p>
        )}
        {importsQuery.data && importsQuery.data.length > 0 && (
          <ol>
            {importsQuery.data.map((run) => (
              <li key={run.id}>
                <details>
                  <summary>
                    <time dateTime={run.started_at}>
                      {formatDate(run.started_at)}
                    </time>
                    {" — "}
                    {run.filenames.join(", ")}
                    {" — "}
                    <Counts run={run} />
                  </summary>
                  <RunDetails run={run} />
                </details>
              </li>
            ))}
          </ol>
        )}
      </section>
    </section>
  );
}
