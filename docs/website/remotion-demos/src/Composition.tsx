import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import React from "react";

const C = {
  bg: "#1E293B",
  fg: "#E2E8F0",
  muted: "#94A3B8",
  accent: "#3B82F6",
  success: "#10B981",
  warning: "#F59E0B",
  error: "#EF4444",
  dim: "#64748B",
  border: "rgba(148,163,184,0.15)",
  surface: "rgba(51,65,85,0.3)",
  prompt: "#64748B",
};

const FONT = "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace";
const FONT_SIZE = 14;

const preStyle: React.CSSProperties = {
  fontFamily: FONT, fontSize: 13, lineHeight: 1.6, color: C.fg, margin: 0,
};

function TerminalHeader({ title = "proxmox" }: { title?: string }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "10px 16px", background: "rgba(15, 23, 42, 0.5)",
      borderBottom: `1px solid ${C.border}`,
    }}>
      <div style={{ width: 12, height: 12, borderRadius: "50%", background: C.error, opacity: 0.7 }} />
      <div style={{ width: 12, height: 12, borderRadius: "50%", background: C.warning, opacity: 0.7 }} />
      <div style={{ width: 12, height: 12, borderRadius: "50%", background: C.success, opacity: 0.7 }} />
      <span style={{ marginLeft: 8, fontSize: 11, color: C.muted, fontFamily: FONT }}>{title}</span>
    </div>
  );
}

function Typewriter({
  children, frame, startFrame = 0, speed = 3, color = C.fg,
}: {
  children: string; frame: number; startFrame?: number; speed?: number; color?: string;
}) {
  const chars = Math.min(Math.floor(Math.max(0, frame - startFrame) / speed), children.length);
  if (chars <= 0) return null;
  const visible = children.slice(0, chars);
  const showCursor = chars < children.length && Math.sin(frame * 0.4) > 0;
  return (
    <span style={{ color, whiteSpace: "pre", fontFamily: FONT, fontSize: FONT_SIZE }}>
      {visible}
      {showCursor ? <span style={{ opacity: 0.6 }}>▊</span> : null}
    </span>
  );
}

function PastPrompt({ text }: { text: string }) {
  return (
    <div style={{ fontFamily: FONT, fontSize: FONT_SIZE, color: C.dim, lineHeight: 1.75 }}>
      <span style={{ color: C.prompt }}>$ </span>{text}
    </div>
  );
}

function FadeIn({
  children, frame, startFrame, duration = 5,
}: {
  children: React.ReactNode; frame: number; startFrame: number; duration?: number;
}) {
  const o = interpolate(frame, [startFrame, startFrame + duration], [0, 1], { extrapolateRight: "clamp" });
  if (o <= 0) return null;
  return <div style={{ opacity: o }}>{children}</div>;
}

function Success({ children }: { children: string }) {
  return (
    <span>
      <span style={{ color: C.success, fontWeight: 700 }}>✓ </span>
      <span style={{ color: C.success }}>{children}</span>
    </span>
  );
}

/** Renders an array of lines from a table, fading in at staggered frames. */
function TableLines({ lines, frame, startFrame, step = 2 }: {
  lines: string[];
  frame: number;
  startFrame: number;
  step?: number;
}) {
  return (
    <>
      {lines.map((line, i) => (
        <FadeIn key={i} frame={frame} startFrame={startFrame + i * step} duration={2}>
          <pre style={preStyle}>{line}</pre>
        </FadeIn>
      ))}
    </>
  );
}

// ── REAL OUTPUT FROM proxmox --output table ──────────────────
// Generated via: python3 -c "from proxmox.output.table_fmt import format_table; ..."
// ANSI stripped, Unicode box-drawing preserved exactly.

const vmListLines = [
  "┏━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━┓",
  "┃ vmid ┃ name       ┃ status  ┃ maxmem      ┃ node  ┃ cpus ┃",
  "┡━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━┩",
  "│ 100  │ webserver  │ running │ 4294967296  │ pve01 │ 2    │",
  "│ 101  │ database   │ running │ 8589934592  │ pve01 │ 4    │",
  "│ 102  │ dev-env    │ stopped │ 1073741824  │ pve02 │ 1    │",
  "│ 103  │ monitoring │ running │ 17179869184 │ pve02 │ 8    │",
  "└──────┴────────────┴─────────┴─────────────┴───────┴──────┘",
];

const vmShowLines = [
  "┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┓",
  "┃ Key         ┃ Value      ┃",
  "┡━━━━━━━━━━━━━╇━━━━━━━━━━━━┩",
  "│ vmid        │ 100        │",
  "│ name        │ webserver  │",
  "│ status      │ running    │",
  "│ node        │ pve01      │",
  "│ memory (MB) │ 4096       │",
  "│ cores       │ 2          │",
  "│ uptime      │ 15d 3h 12m │",
  "└─────────────┴────────────┘",
];

const nodeListLines = [
  "┏━━━━━━━┳━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┓",
  "┃ node  ┃ status  ┃ cpu  ┃ maxmem      ┃ uptime  ┃",
  "┡━━━━━━━╇━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━┩",
  "│ pve01 │ online  │ 0.15 │ 68719476736 │ 2592000 │",
  "│ pve02 │ online  │ 0.08 │ 68719476736 │ 1296000 │",
  "│ pve03 │ offline │ 0    │ 68719476736 │ 0       │",
  "└───────┴─────────┴──────┴─────────────┴─────────┘",
];

const clusterLines = [
  "┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓",
  "┃ type    ┃ name    ┃ id              ┃ nodes ┃ quorate ┃ version ┃",
  "┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩",
  "│ cluster │ proxmox │ cluster/proxmox │ 3     │ 1       │ 8       │",
  "│ node    │ pve01   │                 │       │         │         │",
  "│ node    │ pve02   │                 │       │         │         │",
  "│ node    │ pve03   │                 │       │         │         │",
  "└─────────┴─────────┴─────────────────┴───────┴─────────┴─────────┘",
];

// ── COMPOSITIONS ──────────────────────────────────────────────

export const VmListDemo = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <TerminalHeader title="terminal — proxmox --output table vm list" />
      <div style={{ padding: "20px 28px" }}>
        <div style={{ fontFamily: FONT, fontSize: FONT_SIZE, lineHeight: 1.75 }}>
          <span style={{ color: C.prompt }}>$ </span>
          <Typewriter frame={frame} startFrame={10} speed={4}>proxmox --output table vm list</Typewriter>
        </div>
        <div style={{ marginTop: 14 }}>
          <TableLines lines={vmListLines} frame={frame} startFrame={40} step={3} />
        </div>
        {frame > 100 && (
          <div style={{ marginTop: 18 }}>
            <PastPrompt text="proxmox --output table vm show 100" />
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

export const VmShowDemo = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <TerminalHeader title="terminal — proxmox --output table vm show 100" />
      <div style={{ padding: "20px 28px" }}>
        <div style={{ fontFamily: FONT, fontSize: FONT_SIZE, lineHeight: 1.75 }}>
          <span style={{ color: C.prompt }}>$ </span>
          <Typewriter frame={frame} startFrame={8} speed={4}>proxmox --output table vm show 100</Typewriter>
        </div>
        <div style={{ marginTop: 14 }}>
          <TableLines lines={vmShowLines} frame={frame} startFrame={32} step={2} />
        </div>
        {frame > 80 && (
          <div style={{ marginTop: 18 }}>
            <PastPrompt text="proxmox --output table vm start 100" />
            <FadeIn frame={frame} startFrame={95} duration={5}>
              <div style={{ fontFamily: FONT, fontSize: FONT_SIZE, lineHeight: 1.75 }}>
                <Success>VM 100 started</Success>
              </div>
            </FadeIn>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

export const NodeListDemo = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <TerminalHeader title="terminal — proxmox --output table node list" />
      <div style={{ padding: "20px 28px" }}>
        <div style={{ fontFamily: FONT, fontSize: FONT_SIZE, lineHeight: 1.75 }}>
          <span style={{ color: C.prompt }}>$ </span>
          <Typewriter frame={frame} startFrame={8} speed={4}>proxmox --output table node list</Typewriter>
        </div>
        <div style={{ marginTop: 14 }}>
          <TableLines lines={nodeListLines} frame={frame} startFrame={32} step={3} />
        </div>
        {frame > 80 && (
          <div style={{ marginTop: 18 }}>
            <PastPrompt text="proxmox --output table node status pve01" />
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

export const ClusterCephDemo = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <TerminalHeader title="terminal — proxmox --output table cluster status" />
      <div style={{ padding: "20px 28px" }}>
        <div style={{ fontFamily: FONT, fontSize: FONT_SIZE, lineHeight: 1.75 }}>
          <span style={{ color: C.prompt }}>$ </span>
          <Typewriter frame={frame} startFrame={8} speed={4}>proxmox --output table cluster status</Typewriter>
        </div>
        <div style={{ marginTop: 14 }}>
          <TableLines lines={clusterLines} frame={frame} startFrame={32} step={3} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const YamlSpecDemo = () => {
  const frame = useCurrentFrame();

  const yamlLines = [
    "# webserver.yaml",
    "name: webserver",
    "node: pve01",
    "memory: 4096",
    "cores: 2",
    'import_from: "local:import/debian-12.qcow2"',
    "citype: nocloud",
    "ciuser: debian",
    "cipassword: ChangeMe123!",
    "sshkeys: ~/.ssh/id_rsa.pub",
    'net0: "virtio,bridge=vmbr0"',
    "nameserver: 1.1.1.1",
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <TerminalHeader title="terminal — proxmox vm create --file" />
      <div style={{ padding: "20px 28px", display: "flex", gap: 48 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: FONT, fontSize: 10, color: C.muted, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>
            webserver.yaml
          </div>
          <div style={{ background: "rgba(15,23,42,0.5)", borderRadius: 6, padding: "14px 18px", border: `1px solid ${C.border}` }}>
            {yamlLines.map((line, i) => (
              <FadeIn key={i} frame={frame} startFrame={20 + i * 6} duration={2}>
                <div style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.9 }}>
                  {line.startsWith("#") ? (
                    <span style={{ color: C.muted }}>{line}</span>
                  ) : line.startsWith("name:") || line.startsWith("node:") || line.startsWith("ci") ? (
                    <><span style={{ color: C.accent }}>{line.split(":")[0]}</span><span style={{ color: C.muted }}>:</span><span style={{ color: C.fg }}>{line.slice(line.indexOf(":"))}</span></>
                  ) : line.startsWith("memory:") || line.startsWith("cores:") ? (
                    <><span style={{ color: C.success }}>{line.split(":")[0]}</span><span style={{ color: C.muted }}>:</span><span style={{ color: C.fg }}>{line.slice(line.indexOf(":"))}</span></>
                  ) : (
                    <span style={{ color: C.fg }}>{line}</span>
                  )}
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: FONT, fontSize: 10, color: C.muted, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>
            commands
          </div>
          <div style={{ background: "rgba(15,23,42,0.5)", borderRadius: 6, padding: "14px 18px", border: `1px solid ${C.border}` }}>
            <FadeIn frame={frame} startFrame={100} duration={3}>
              <div style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.9 }}>
                <span style={{ color: C.prompt }}>$ </span>
                <span style={{ color: C.fg }}>proxmox vm create --file</span>
              </div>
              <div style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.9, paddingLeft: 16 }}>
                <span style={{ color: C.fg }}>webserver.yaml</span>
              </div>
            </FadeIn>
            <FadeIn frame={frame} startFrame={112} duration={3}>
              <div style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.9, marginTop: 8 }}>
                <span style={{ color: C.muted }}>→ Override:</span>
              </div>
              <div style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.9 }}>
                <span style={{ color: C.prompt }}>$ </span>
                <span style={{ color: C.fg }}>proxmox vm create --file</span>
              </div>
              <div style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.9, paddingLeft: 16 }}>
                <span style={{ color: C.fg }}>webserver.yaml --name staging</span>
              </div>
              <div style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.9, paddingLeft: 16 }}>
                <span style={{ color: C.fg }}>--memory 8192</span>
              </div>
            </FadeIn>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
