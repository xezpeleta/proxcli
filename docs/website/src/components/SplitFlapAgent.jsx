import React, { useEffect, useState, useRef, useCallback } from 'react'

// ---- ASCII BIG LETTERS (7 rows) ----
const LETTERS_7 = {
  ' ': ['      ', '      ', '      ', '      ', '      ', '      ', '      '],
  'A': [
    ' ████ ',
    '██  ██',
    '██  ██',
    '██████',
    '██  ██',
    '██  ██',
    '██  ██',
  ],
  'G': [
    ' █████',
    '██    ',
    '██    ',
    '██ ███',
    '██  ██',
    '██  ██',
    ' ████ ',
  ],
  'E': [
    '██████',
    '██    ',
    '██    ',
    '█████ ',
    '██    ',
    '██    ',
    '██████',
  ],
  'N': [
    '██  ██',
    '███ ██',
    '██████',
    '██ ███',
    '██  ██',
    '██  ██',
    '██  ██',
  ],
  'S': [
    ' ████ ',
    '██  ██',
    '██    ',
    ' ████ ',
    '    ██',
    '██  ██',
    ' ████ ',
  ],
  'T': [
    '██████',
    '  ██  ',
    '  ██  ',
    '  ██  ',
    '  ██  ',
    '  ██  ',
    '  ██  ',
  ],
}

const HEIGHT = 7

function gridForWord(word) {
  const chars = [...word]
  const rows = []
  for (let r = 0; r < HEIGHT; r++) {
    const rowParts = chars.map(ch => {
      const letter = LETTERS_7[ch]
      return letter ? letter[r] : '      '
    })
    rows.push(rowParts.join(' '))
  }
  return rows
}

const DEBRIS_CHARS = '01!?#$%&@<>{}[]/\\|*^~'

const ROBOT_HEAD = [
  '                                     ==-                                      ',
  '                                   =======                                    ',
  '                                  ===###==:                                   ',
  '                                  -===*===                                    ',
  '                                    ====-                                     ',
  '                                     ==-                                      ',
  '                                     ==-                                      ',
  '                                     ==-                                      ',
  '                  ========================================-                   ',
  '                 ==========================================:                  ',
  '                 ==========================================-                  ',
  '                 ==========================================-                  ',
  '             *###=========##*+*#============+##+*#==========###=              ',
  '            =####=======#=      .%=========%       %========####              ',
  '            +####=======%        -========%         %=======####              ',
  '            +####=======%        -========%         %=======####              ',
  '            +####=======#-      .%====+====%       %========####              ',
  '            +####=========##+=*#=====##*====+#*+*#==========####              ',
  '            +####===================####*===================####              ',
  '            +####===========================================####              ',
  '            +####===========================================####              ',
  '            +####============:+:::+:::+:::+:::+:============####              ',
  '            +####==========   *   #   #   #   #  .==========####              ',
  '             ####==========   #   #   #   #   #  .==========####              ',
  '              :##============:#:::#:::#:::#:::#:============##                ',
  '                 ==========================================-                  ',
  '                 ==========================================-                  ',
  '                 .=========================================                   ',
]

function randomDebrisChar() {
  return DEBRIS_CHARS[Math.floor(Math.random() * DEBRIS_CHARS.length)]
}

const HUMAN_DURATION = 2800
const AGENT_DURATION = 3200
const TRANSITION_MS = 1200

// ---- Main Component ----
export default function SplitFlapAgent() {
  const [phase, setPhase] = useState('human')
  const [fadeHuman, setFadeHuman] = useState(1)
  const [fadeAscii, setFadeAscii] = useState(0)
  const [humanText, setHumanText] = useState('HUMANS')
  const [glitchX, setGlitchX] = useState(0)
  const [particles, setParticles] = useState([])
  const timerRef = useRef(null)

  const agentGrid = useRef(gridForWord('AGENTS'))

  // ---- Transition ----
  const startTransition = useCallback((dir) => {
    setPhase(dir)
    const startTime = Date.now()
    const fromWord = dir === 'toAgent' ? 'HUMANS' : 'AGENTS'

    timerRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / TRANSITION_MS, 1)

      const keepCount = Math.max(0, Math.floor((1 - progress) * fromWord.length))
      let scrambled = ''
      for (let i = 0; i < fromWord.length; i++) {
        scrambled += i < keepCount
          ? fromWord[i]
          : (Math.random() > 0.5 ? fromWord[i] : randomDebrisChar())
      }
      if (progress > 0.3) {
        for (let j = 0; j < Math.floor(progress * 6); j++) scrambled += randomDebrisChar()
      }
      setHumanText(scrambled)

      const eased = progress < 0.5
        ? 2 * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 2) / 2

      if (dir === 'toAgent') {
        setFadeHuman(Math.max(0, 1 - eased * 1.15))
        setFadeAscii(Math.min(1, eased * 1.15))
      } else {
        setFadeAscii(Math.max(0, 1 - eased * 1.15))
        setFadeHuman(Math.min(1, eased * 1.15))
      }

      if (progress >= 1) {
        clearInterval(timerRef.current)
        setPhase(dir === 'toAgent' ? 'agent' : 'human')
        if (dir === 'toHuman') setHumanText('HUMANS')
      }
    }, 30)
  }, [])

  // ---- Loop ----
  useEffect(() => {
    let alive = true
    const run = async () => {
      while (alive) {
        setPhase('human')
        setFadeHuman(1)
        setFadeAscii(0)
        setHumanText('HUMANS')
        await sleep(HUMAN_DURATION)
        if (!alive) break

        startTransition('toAgent')
        await sleep(TRANSITION_MS + 100)
        if (!alive) break

        await sleep(AGENT_DURATION)
        if (!alive) break

        startTransition('toHuman')
        await sleep(TRANSITION_MS + 100)
      }
    }
    run()
    return () => { alive = false; if (timerRef.current) clearInterval(timerRef.current) }
  }, [startTransition])

  // ---- Glitch + particles when ASCII visible ----
  useEffect(() => {
    if (fadeAscii < 0.2) return

    let glitchT
    const scheduleGlitch = () => {
      glitchT = setTimeout(() => {
        setGlitchX(Math.random() > 0.5 ? 2 : -2)
        setTimeout(() => setGlitchX(0), 70)
        scheduleGlitch()
      }, 1000 + Math.random() * 3000)
    }
    scheduleGlitch()

    const pTimer = setInterval(() => {
      setParticles(prev => [...prev.slice(-14), {
        id: Date.now() + Math.random(),
        char: randomDebrisChar(),
        x: 5 + Math.random() * 90,
        y: 10 + Math.random() * 80,
        life: 500 + Math.random() * 1000,
        born: Date.now(),
      }])
    }, 300)

    const cTimer = setInterval(() => {
      const now = Date.now()
      setParticles(prev => prev.filter(p => now - p.born < p.life))
    }, 400)

    return () => {
      clearTimeout(glitchT)
      clearInterval(pTimer)
      clearInterval(cTimer)
    }
  }, [fadeAscii])

  const isHuman = phase === 'human' || phase === 'toAgent'
  const isAgent = phase === 'agent' || phase === 'toHuman'

  return (
    <div
      className="relative h-full flex items-center overflow-hidden"
      style={{
        transform: `translateX(${glitchX}px)`,
        transition: 'transform 0.06s',
      }}
    >
      {/* Floating debris */}
      {particles.map(p => {
        const elapsed = Date.now() - p.born
        if (elapsed >= p.life) return null
        return (
          <span
            key={p.id}
            className="absolute font-mono text-[11px] pointer-events-none select-none z-10"
            style={{
              color: '#E6C34A',
              opacity: Math.max(0, 0.5 * (1 - elapsed / p.life)),
              transform: `translateY(${-20 * (elapsed / p.life)}px)`,
            }}
          >
            {p.char}
          </span>
        )
      })}

      {/* HUMAN: warm serif */}
      <div style={{
        opacity: fadeHuman,
        transition: 'opacity 0.15s',
        position: isAgent ? 'absolute' : 'static',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        visibility: fadeHuman < 0.02 ? 'hidden' : 'visible',
      }}>
        <span
          className="font-serif italic inline-flex items-baseline gap-2"
          style={{
            color: '#60A5FA',
            fontSize: 'clamp(2rem, 8vw, 5rem)',
            fontWeight: 400,
            letterSpacing: '0.02em',
            textShadow: '0 0 40px rgba(96,165,250,0.3), 0 0 80px rgba(96,165,250,0.1)',
          }}
        >
          <span>{isHuman ? humanText : 'HUMANS'}</span>
          <span
            className="text-tertiary/60"
            style={{ fontSize: 'clamp(1.5rem, 6vw, 3.5rem)', fontWeight: 300, color: '#60A5FA', opacity: 0.6 }}
          >
            &
          </span>
        </span>
      </div>

      {/* AGENT: big ASCII + robot head */}
      <pre
        className="font-mono leading-none whitespace-pre select-none"
        style={{
          color: '#E6C34A',
          fontSize: 'clamp(6px, 2vw, 15px)',
          opacity: fadeAscii,
          transition: 'opacity 0.15s',
          position: isHuman ? 'absolute' : 'static',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          visibility: fadeAscii < 0.02 ? 'hidden' : 'visible',
          margin: 0,
        }}
      >
        {agentGrid.current.map((row, i) => (
          <div key={i}>{row}</div>
        ))}
      </pre>

      {/* Robot — only visible on md+ screens */}
      <pre
        className="hidden md:block font-mono leading-none whitespace-pre select-none"
        style={{
          color: '#E6C34A',
          fontSize: 'clamp(2.5px, 0.55vw, 4.5px)',
          opacity: fadeAscii,
          transition: 'opacity 0.15s',
          position: isHuman ? 'absolute' : 'static',
          margin: 0,
          marginLeft: 'clamp(12px, 2vw, 32px)',
          visibility: fadeAscii < 0.02 ? 'hidden' : 'visible',
        }}
      >
        {ROBOT_HEAD.map((row, i) => (
          <div key={i}>{row}</div>
        ))}
      </pre>

    </div>
  )
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
