import React, { useState, useRef } from "react";
import {
  Drawer,
  DrawerHeader,
  DrawerHeaderTitle,
  DrawerBody,
  Button,
  Input,
  Text,
  Badge,
  Card,
  Spinner,
} from "@fluentui/react-components";
import {
  Dismiss24Regular,
  ArrowUpload24Regular,
  ArrowSync24Regular,
  Search24Regular,
  DocumentPdf24Regular,
  DocumentText24Regular,
} from "@fluentui/react-icons";
import type { KnowledgeStats } from "../types";
import { uploadDocument, queryKnowledge, reindexDirectory } from "../api";

interface KnowledgeDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  stats: KnowledgeStats | null;
  onRefreshStats: () => void;
}

export const KnowledgeDrawer: React.FC<KnowledgeDrawerProps> = ({
  isOpen,
  onClose,
  stats,
  onRefreshStats,
}) => {
  const [testQuery, setTestQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTestSearch = async () => {
    if (!testQuery.trim()) return;
    setIsSearching(true);
    try {
      const data = await queryKnowledge(testQuery);
      setSearchResults(data.results || []);
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setUploadStatus("Uploading & vectorizing document...");
    try {
      const res = await uploadDocument(file);
      setUploadStatus(`Success! Added ${res.chunks_added} chunks to Vector Store.`);
      onRefreshStats();
    } catch (err: any) {
      setUploadStatus(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleReindex = async () => {
    setIsUploading(true);
    setUploadStatus("Re-indexing data/raw directory...");
    try {
      const res = await reindexDirectory();
      setUploadStatus(`Indexed ${res.chunks_indexed} chunks.`);
      onRefreshStats();
    } catch (err: any) {
      setUploadStatus(`Reindex failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Drawer
      type="overlay"
      separator
      open={isOpen}
      onOpenChange={(_, { open }) => !open && onClose()}
      position="end"
      size="medium"
    >
      <DrawerHeader>
        <DrawerHeaderTitle
          action={
            <Button
              appearance="subtle"
              aria-label="Close"
              icon={<Dismiss24Regular />}
              onClick={onClose}
            />
          }
        >
          Knowledge Base & RAG Index
        </DrawerHeaderTitle>
      </DrawerHeader>

      <DrawerBody className="knowledge-drawer-body">
        {/* Vector Store Overview Card */}
        <Card className="kb-stats-card">
          <div className="kb-stats-grid">
            <div className="stat-item">
              <Text size={500} weight="bold" className="stat-number">
                {stats?.total_chunks ?? 0}
              </Text>
              <Text size={200} className="stat-label">
                Total Chunks
              </Text>
            </div>
            <div className="stat-item">
              <Text size={500} weight="bold" className="stat-number">
                {stats?.sources_count ?? 0}
              </Text>
              <Text size={200} className="stat-label">
                Documents
              </Text>
            </div>
            <div className="stat-item">
              <Badge appearance="tint" color="brand">
                {stats?.vector_backend || "Vector DB"}
              </Badge>
              <Text size={100} className="stat-label">
                Backend
              </Text>
            </div>
          </div>

          <div className="kb-sources-list">
            <Text size={200} weight="semibold">
              Indexed Documents:
            </Text>
            {stats?.sources && stats.sources.length > 0 ? (
              <div className="sources-chips">
                {stats.sources.map((s, idx) => (
                  <Badge key={idx} appearance="outline" shape="rounded">
                    {s.endsWith(".pdf") ? (
                      <DocumentPdf24Regular style={{ fontSize: 14 }} />
                    ) : (
                      <DocumentText24Regular style={{ fontSize: 14 }} />
                    )}
                    {s}
                  </Badge>
                ))}
              </div>
            ) : (
              <Text size={200} italic>
                No documents uploaded yet.
              </Text>
            )}
          </div>

          <div className="kb-actions-row">
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.pdf,.json"
              style={{ display: "none" }}
              onChange={handleFileUpload}
              disabled={isUploading}
            />
            <Button
              appearance="primary"
              icon={<ArrowUpload24Regular />}
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
            >
              Upload Document
            </Button>

            <Button
              appearance="secondary"
              icon={<ArrowSync24Regular />}
              onClick={handleReindex}
              disabled={isUploading}
            >
              Sync Directory
            </Button>
          </div>

          {uploadStatus && (
            <Text size={200} className="upload-status-text">
              {uploadStatus}
            </Text>
          )}
        </Card>

        {/* Semantic Search Inspector */}
        <div className="kb-search-section">
          <Text size={300} weight="semibold">
            Test Vector Retrieval & Similarity
          </Text>
          <div className="kb-search-input-row">
            <Input
              placeholder="Search concepts across indexed documents..."
              value={testQuery}
              onChange={(_, data) => setTestQuery(data.value)}
              onKeyDown={(e) => e.key === "Enter" && handleTestSearch()}
              contentAfter={
                <Button
                  appearance="transparent"
                  icon={<Search24Regular />}
                  onClick={handleTestSearch}
                />
              }
            />
          </div>

          {isSearching && <Spinner size="small" label="Querying vector store..." />}

          <div className="kb-search-results">
            {searchResults.map((res, idx) => (
              <Card key={idx} className="chunk-preview-card">
                <div className="chunk-header">
                  <Badge appearance="filled" color="informative" size="small">
                    Score: {Math.round((res.score || 0) * 100)}%
                  </Badge>
                  <Text size={100} weight="semibold">
                    {res.source} {res.page ? `(Page ${res.page})` : ""}
                  </Text>
                </div>
                <Text size={200} className="chunk-content-preview">
                  {res.content}
                </Text>
              </Card>
            ))}
          </div>
        </div>
      </DrawerBody>
    </Drawer>
  );
};
