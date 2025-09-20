# Minimal curated topic map for MVP – expand as needed.
# Keys = canonical topic id, values = curated, trusted links.
TOPIC_MAP = {
    "linear_algebra.eigenvalues": {
        "keywords": ["eigenvalue","eigenvalues","eigenvectors","diagonalization","la hw","linear algebra"],
        "resources": [
            {
                "type": "video",
                "title": "Khan Academy — Intro to eigenvalues",
                "url": "https://www.khanacademy.org/math/linear-algebra/alternate-bases/eigen-everything/v/introduction-to-eigenvalues-and-eigenvectors",
                "why": "Short visual primer to refresh the concept."
            },
            {
                "type": "notes",
                "title": "MIT OCW 18.06 — Lecture Notes: Eigenvalues & Eigenvectors",
                "url": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/lecture-16-eigenvalues-and-eigenvectors/",
                "why": "Concise definitions and worked examples."
            },
            {
                "type": "practice",
                "title": "Eigenvalue practice problems",
                "url": "https://people.math.harvard.edu/~knill/linearalgebra3/shortquiz/quiz10.pdf",
                "why": "Exam-style drills to build fluency."
            }
        ],
        "practice": [
            {
                "prompt": "Find eigenvalues of A = [[2,1],[1,2]].",
                "solution_url": "https://math.stackexchange.com/questions/82678/eigenvalues-of-matrix-2-1-1-2"
            },
            {
                "prompt": "Show that for a triangular matrix, eigenvalues are the diagonal entries."
            }
        ],
        "ideas": [
            "Diagonalization as a change of basis",
            "Characteristic polynomial det(A−λI)=0"
        ]
    },
    "mech.dynamics.free_body": {
        "keywords": ["free body diagram","fbd","dynamics","lab report","me","mechanics","forces"],
        "resources": [
            {
                "type": "video",
                "title": "Engineer4Free — Free Body Diagrams",
                "url": "https://www.youtube.com/watch?v=jg2T1qk9uN0",
                "why": "Clear walk-through of FBD basics with examples."
            },
            {
                "type": "notes",
                "title": "Georgia Tech — Statics & Dynamics Notes (FBD)",
                "url": "https://sebokht.wpenginepowered.com/wp-content/uploads/2019/04/Free-Body-Diagrams.pdf",
                "why": "Step-by-step checklist for correct FBDs."
            },
            {
                "type": "practice",
                "title": "Dynamics practice set (forces & motion)",
                "url": "https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/pages/problem-solving-help/practice-problems/",
                "why": "Targeted problems to test understanding."
            }
        ],
        "practice": [
            {"prompt": "Draw the FBD for a block on an inclined plane with friction μ."},
            {"prompt": "Write ΣF=ma along/normal to the plane and solve for acceleration."}
        ],
        "ideas": [
            "Resolve forces into components",
            "Newton’s 2nd law along chosen axes"
        ]
    },
    "probability.bayes": {
        "keywords": ["bayes","conditional probability","quiz prep","probability"],
        "resources": [
            {
                "type": "video",
                "title": "3Blue1Brown — Bayes theorem",
                "url": "https://www.youtube.com/watch?v=HZGCoVF3YvM",
                "why": "Visual intuition for Bayes’ theorem."
            },
            {
                "type": "article",
                "title": "Wikipedia — Bayes' theorem (overview)",
                "url": "https://en.wikipedia.org/wiki/Bayes%27_theorem",
                "why": "Definitions and canonical examples."
            },
            {
                "type": "practice",
                "title": "Bayes practice problems",
                "url": "https://people.math.umass.edu/~lavine/Book/book.pdf#page=51",
                "why": "Problems with worked solutions."
            }
        ],
        "practice": [
            {"prompt": "Solve a medical test false positive problem using Bayes."},
            {"prompt": "Compute P(A|B) for a two-urn draw scenario."}
        ],
        "ideas": [
            "Likelihood vs prior",
            "Normalization by evidence"
        ]
    },
    "writing.essay_argument": {
        "keywords": ["essay","draft","argument","thesis","introduction","eng"],
        "resources": [
            {
                "type":"notes",
                "title":"Purdue OWL — Argumentative Essays",
                "url":"https://owl.purdue.edu/owl/general_writing/academic_writing/essay_writing/argumentative_essays.html",
                "why":"Structure, thesis, and evidence guidelines."
            },
            {
                "type":"article",
                "title":"Harvard — Writing a Thesis",
                "url":"https://writingcenter.fas.harvard.edu/pages/developing-thesis",
                "why":"Concrete examples of strong theses."
            },
            {
                "type":"notes",
                "title":"UChicago — Outlining Strategies",
                "url":"https://writing-program.uchicago.edu/undergraduates/outlining",
                "why":"Blueprint your essay fast."
            }
        ],
        "practice":[
            {"prompt":"Draft a 1-sentence thesis on: 'The ethics of autonomous vehicles'."},
            {"prompt":"Outline 3 supporting paragraphs; list one counterargument."}
        ],
        "ideas":[
            "Thesis first, evidence second",
            "Counterargument strengthens credibility"
        ]
    },
        "linear_algebra.eigenvalues": {
        "keywords": ["eigenvalue","eigenvalues","eigenvectors","diagonalization","la hw","linear algebra"],
        "resources": [
            {"type":"video","title":"Khan Academy — Intro to eigenvalues","url":"https://www.khanacademy.org/math/linear-algebra/alternate-bases/eigen-everything/v/introduction-to-eigenvalues-and-eigenvectors","why":"Short visual primer to refresh the concept."},
            {"type":"notes","title":"MIT OCW 18.06 — Lecture Notes: Eigenvalues & Eigenvectors","url":"https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/lecture-16-eigenvalues-and-eigenvectors/","why":"Concise definitions and worked examples."},
            {"type":"practice","title":"Eigenvalue practice problems","url":"https://people.math.harvard.edu/~knill/linearalgebra3/shortquiz/quiz10.pdf","why":"Exam-style drills to build fluency."}
        ],
        "practice": [
            {"prompt":"Find eigenvalues of A = [[2,1],[1,2]].","solution_url":"https://math.stackexchange.com/questions/82678/eigenvalues-of-matrix-2-1-1-2"},
            {"prompt":"Show that for a triangular matrix, eigenvalues are the diagonal entries."}
        ],
        "ideas": ["Diagonalization as a change of basis","Characteristic polynomial det(A−λI)=0"]
    },

    "math.differential_equations": {
        "keywords": ["ode","initial value problem","first order","second order","engineering math","ivp"],
        "resources": [
            {"type":"video","title":"Khan Academy — First-order differential equations","url":"https://www.khanacademy.org/math/differential-equations/first-order-differential-equations","why":"Clear primer on 1st-order methods."},
            {"type":"notes","title":"MIT OCW 18.03 — Differential Equations","url":"https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","why":"Comprehensive notes + problems."},
            {"type":"practice","title":"MIT OCW 18.03 — Problem sets","url":"https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/pages/unit-i-first-order-differential-equations/problem-set/","why":"Exam-style exercises."}
        ],
        "practice": [
            {"prompt": "Solve dy/dx = 2y with y(0)=1."},
            {"prompt": "Find the general solution of y'' + 4y = 0 and classify the roots."}
        ],
        "ideas": ["Separation of variables → exponential solutions","Characteristic equation for linear ODEs"]
    },

    # --- Thermo / Fluids / Heat ---
    "thermo.basics": {
        "keywords": ["thermodynamics","energy balance","first law","second law","entropy","bh20a0720"],
        "resources": [
            {"type":"video","title":"Khan Academy — Thermodynamics","url":"https://www.khanacademy.org/science/physics/thermodynamics","why":"Concept overview with simple examples."},
            {"type":"notes","title":"MIT OCW — Thermodynamics (2.05)","url":"https://ocw.mit.edu/courses/2-05-thermodynamics-fall-2013/","why":"Formal treatment + problem sets."},
            {"type":"practice","title":"MIT OCW 2.05 — Assignments","url":"https://ocw.mit.edu/courses/2-05-thermodynamics-fall-2013/pages/assignments/","why":"Worked problems on energy balances."}
        ],
        "practice": [
            {"prompt": "State the first law for a closed system and apply it to a piston compression."},
            {"prompt": "A system absorbs 200 J heat and does 50 J work. Compute ΔU with sign convention."}
        ],
        "ideas": ["ΔU = Q − W (closed system)","Entropy production ≥ 0 (irreversibility)"]
    },

    "fluid_mech.basics": {
        "keywords": ["fluid mechanics","continuity","bernoulli","bh40a1401","bh40a1453","pressure","viscosity"],
        "resources": [
            {"type":"video","title":"Khan Academy — Fluid dynamics","url":"https://www.khanacademy.org/science/physics/fluids","why":"Intro to continuity, Bernoulli, pressure."},
            {"type":"notes","title":"MIT OCW 2.25 — Fluid Mechanics (notes)","url":"https://ocw.mit.edu/courses/2-25-advanced-fluid-mechanics-fall-2013/","why":"Formal derivations and examples."},
            {"type":"practice","title":"Fluid mechanics problems (MIT OCW)","url":"https://ocw.mit.edu/courses/2-25-advanced-fluid-mechanics-fall-2013/pages/assignments/","why":"Practice with worked solutions."}
        ],
        "practice": [
            {"prompt":"Use Bernoulli between two points in a horizontal pipe with changing area to find velocity change."},
            {"prompt":"Compute Reynolds number and state flow regime for water at 20°C in a 2 cm pipe at 1 m/s."}
        ],
        "ideas": ["Continuity: A1V1=A2V2","Bernoulli along a streamline","Laminar vs turbulent via Reynolds number"]
    },

    "heat_transfer.basics": {
        "keywords": ["heat transfer","conduction","convection","radiation","bh20a0310","fourier","newton cooling"],
        "resources": [
            {"type":"video","title":"Khan Academy — Heat transfer","url":"https://www.khanacademy.org/science/physics/thermodynamics","why":"Conceptual overview of modes."},
            {"type":"notes","title":"MIT OCW 2.086 — Numerical Heat Transfer (notes)","url":"https://ocw.mit.edu/courses/2-086-numerical-computation-for-mechanical-engineers-fall-2012/","why":"Engineering context and examples."},
            {"type":"practice","title":"Example problems (UCD heat transfer)","url":"https://www.ucd.ie/mecheng/study/undergraduate/heattransfer/","why":"Worked example set."}
        ],
        "practice": [
            {"prompt":"Steady 1D conduction across a wall: given k,A,ΔT,L, compute heat rate q."},
            {"prompt":"Use Newton’s law of cooling to estimate convective heat loss from a cylinder."}
        ],
        "ideas": ["Fourier’s law q=-kA dT/dx","Newton cooling q=hA(T_s−T_∞)","Radiation q=εσA(T^4−T_∞^4)"]
    },

    # --- Circuits / Electronics / EMC ---
    "circuits.dc_ac_basics": {
        "keywords": ["ohm's law","kcl","kvl","dc circuits","ac circuits","phasor","impedance","bl30a0001"],
        "resources": [
            {"type":"video","title":"Khan Academy — Circuits fundamentals","url":"https://www.khanacademy.org/science/physics/circuits-topic","why":"Intro to V, I, R and basic laws."},
            {"type":"notes","title":"All About Circuits — Textbook","url":"https://www.allaboutcircuits.com/textbook/","why":"Readable DC & AC reference with diagrams."},
            {"type":"practice","title":"All About Circuits — Worksheets","url":"https://www.allaboutcircuits.com/worksheets/","why":"Worksheets covering KCL/KVL and impedance."}
        ],
        "practice": [
            {"prompt": "Find the current for a 12 V source across 6 Ω; then split a series+parallel combo."},
            {"prompt": "For a 10∠0° V AC source and Z=5∠30° Ω, find the phasor current I."}
        ],
        "ideas": ["Ohm’s law V=IR; KCL/KVL govern node/loop sums","AC uses phasors; impedance adds vectorially"]
    },

    "electronics.basics": {
        "keywords": ["electronics","bl50a0021","diode","bjt","op-amp","filters","basic electronics 1"],
        "resources": [
            {"type":"video","title":"Khan Academy — Semiconductor diodes & transistors","url":"https://www.khanacademy.org/science/electrical-engineering/semiconductors","why":"Visual intro to devices."},
            {"type":"notes","title":"All About Circuits — Semiconductors","url":"https://www.allaboutcircuits.com/textbook/semiconductors/","why":"Readable device explanations."},
            {"type":"practice","title":"Op-amp problems (Analog)","url":"https://www.analog.com/en/education/education-library/op-amp-applications.html","why":"Application-style practice."}
        ],
        "practice": [
            {"prompt":"Compute the output of an inverting op-amp with Rin=10k, Rf=100k, Vin=0.2 V."},
            {"prompt":"Sketch the I–V curve of an ideal diode and identify forward conduction region."}
        ],
        "ideas": ["Diode equation (idealized)","Op-amp golden rules (ideal)","RC filter cutoff f_c=1/(2πRC)"]
    },

    "emc.basics": {
        "keywords": ["emc","coupling","capacitive","inductive","galvanic","bl50a0210","shielding","grounding"],
        "resources": [
            {"type":"video","title":"EMC Basics — Keysight (seminar)","url":"https://www.youtube.com/watch?v=9b4t3d6fC50","why":"Practical overview of coupling paths."},
            {"type":"notes","title":"EMC Fundamentals (TI app note)","url":"https://www.ti.com/lit/an/szza009/szza009.pdf","why":"Concise fundamentals and layouts."},
            {"type":"practice","title":"EMC practice Qs (university sets)","url":"https://emcprinciples.com/","why":"Concept checks and examples."}
        ],
        "practice": [
            {"prompt":"Classify a noise path as capacitive, inductive, or galvanic for two cables running in parallel."},
            {"prompt":"Suggest two mitigations for SMPS high di/dt ringing on a sensor line."}
        ],
        "ideas": ["Three coupling types (C/L/galvanic)","Loop area ↑ → inductive coupling ↑","Low-Z return paths & decoupling"]
    },

    # --- Mechanics / Mechatronics ---
    "mech.statics": {
        "keywords": ["statics","free body diagram","fbd","beam reactions","supports","equilibrium","bk80a4000"],
        "resources": [
            {"type": "video","title": "Engineer4Free — Free Body Diagrams","url": "https://www.youtube.com/watch?v=jg2T1qk9uN0","why": "FBD workflow and common mistakes."},
            {"type": "notes","title": "Georgia Tech — FBD guide","url": "https://sebokht.wpenginepowered.com/wp-content/uploads/2019/04/Free-Body-Diagrams.pdf","why": "Checklist for correct FBDs."},
            {"type": "practice","title": "MIT OCW 2.01 — Assignments","url": "https://ocw.mit.edu/courses/2-01-elements-of-structures-fall-2008/pages/assignments/","why": "Beam reactions and equilibrium problems."}
        ],
        "practice": [
            {"prompt": "Draw the FBD of a simply supported beam with a mid-span point load; solve for reactions."},
            {"prompt": "Verify ΣFx=0, ΣFy=0, ΣM=0 for an L-bracket with two applied forces."}
        ],
        "ideas": ["Equilibrium: ΣF=0, ΣM=0","Model supports correctly (pins, rollers, fixed)"]
    },

    "mechatronics.intro": {
        "keywords": ["mechatronics","sensors","actuators","bk10a6202","control","embedded"],
        "resources": [
            {"type":"video","title":"Mechatronics overview","url":"https://www.youtube.com/watch?v=U23WfG0K8nA","why":"Systems view: sensors→controller→actuators."},
            {"type":"notes","title":"MIT OpenCourseWare — Mechatronics notes","url":"https://ocw.mit.edu/search/?q=mechatronics","why":"Lecture notes & labs."},
            {"type":"practice","title":"Simple mechatronics lab ideas","url":"https://learn.adafruit.com/","why":"Sensor/actuator mini-labs."}
        ],
        "practice": [
            {"prompt":"Design a block diagram: sensor → microcontroller → motor driver → DC motor (with feedback)."},
            {"prompt":"Pick a sensor for measuring shaft speed and justify the interface approach."}
        ],
        "ideas": ["Sense→Think→Act loop","Closed-loop control benefits","Interface (analog, I2C, SPI, PWM)"]
    },

    # --- Energy / Renewables ---
    "renewables.basics": {
        "keywords": ["renewable energy","bh40a0102","bl40a2601","wind","solar","pv","business"],
        "resources": [
            {"type":"video","title":"Solar PV basics — Khan Academy","url":"https://www.khanacademy.org/science/physics/semiconductors-topic/diodes/a/solar-cells","why":"PV cell working principle."},
            {"type":"notes","title":"NREL — PV basics","url":"https://www.nrel.gov/research/pv.html","why":"Authoritative PV reference."},
            {"type":"practice","title":"Wind/PV sizing examples","url":"https://www.pveducation.org/","why":"Worked example library."}
        ],
        "practice": [
            {"prompt":"Estimate energy yield from a 5 kW PV system in a location with 1000 kWh/m²·yr insolation (rough)."},
            {"prompt":"Compute tip-speed ratio for a wind turbine with R=20 m at 12 rpm and V=8 m/s."}
        ],
        "ideas": ["PV IV curve & MPPT","Capacity factor concept","Wind power ∝ ρ A V^3"]
    },

    "energy_systems.overview": {
        "keywords": ["energy systems","bh50a0220","generation","grid","storage","dispatch"],
        "resources": [
            {"type":"video","title":"How the Grid Works","url":"https://www.youtube.com/watch?v=Fj8G9dI2PXo","why":"Visual overview of power systems."},
            {"type":"notes","title":"MIT OCW 6.061 — Intro to Power Systems","url":"https://ocw.mit.edu/courses/6-061-introduction-to-electric-power-systems-spring-2011/","why":"Lecture notes and problem sets."},
            {"type":"practice","title":"Simple dispatch problems","url":"https://ocw.mit.edu/courses/6-061-introduction-to-electric-power-systems-spring-2011/pages/assignments/","why":"Hands-on calculations."}
        ],
        "practice": [
            {"prompt":"Draw a block diagram: generation → transmission → distribution → load, with typical voltages."},
            {"prompt":"Explain baseload vs peak vs intermediate plants with one example each."}
        ],
        "ideas": ["Load curve & dispatch","Grid stability (frequency/voltage)","Role of storage"]
    },

        # --- Materials / Writing / Physics ---
        "materials.intro": {
            "keywords": ["materials","bk10a5900","stress strain","young modulus","failure","metals polymers ceramics"],
            "resources": [
                {"type":"video","title":"Materials 101 — Intro","url":"https://www.youtube.com/watch?v=4uY9U5fZ3vQ","why":"High-level survey of classes."},
                {"type":"notes","title":"MIT OCW 3.091 — Introduction to Solid State Chemistry","url":"https://ocw.mit.edu/courses/3-091-introduction-to-solid-state-chemistry-fall-2018/","why":"Covers bonding → properties."},
                {"type":"practice","title":"Stress–strain problems (examples)","url":"https://mechanicalc.com/reference/stress-strain","why":"Short exercises with formulas."}
            ],
            "practice": [
                {"prompt":"Given σ–ε data, estimate Young’s modulus and yield stress."},
                {"prompt":"Compare ductile vs brittle fracture features on a stress–strain curve."}
            ],
            "ideas": ["Hooke’s law σ=Eε (linear elastic)","Toughness = area under curve","Microstructure ↔ properties"]
        },

        "writing.academic": {
            "keywords": ["academic writing","les","reports","structure","thesis","ke00bz81","technical documentation"],
            "resources": [
                {"type":"notes","title":"Purdue OWL — Academic Writing","url":"https://owl.purdue.edu/owl/general_writing/academic_writing/index.html","why":"Structure and style."},
                {"type":"notes","title":"UW — Lab Report Guidelines","url":"https://courses.washington.edu/chem162/LabManual/Style.html","why":"Scientific report specifics."},
                {"type":"practice","title":"Thesis and outline drills","url":"https://writingcenter.fas.harvard.edu/pages/essay-structure","why":"Quick exercises on structure."}
            ],
            "practice": [
                {"prompt":"Write a 1-sentence thesis for: ‘Impact of heat pumps on Nordic grids’."},
                {"prompt":"Outline IMRaD sections for a 4-page lab report on pipe flow."}
            ],
            "ideas": ["IMRaD structure","Evidence > claims","Signposting topic sentences"]
        },

        "physics.electricity_magnetism": {
            "keywords": ["electricity","magnetism","bl30a0350","maxwell","faraday","inductance","capacitance"],
            "resources": [
                {"type":"video","title":"Khan Academy — Electricity and Magnetism","url":"https://www.khanacademy.org/science/physics/electricity-and-magnetism","why":"Concept sequences for E&M."},
                {"type":"notes","title":"MIT OCW 8.02 — E&M Notes","url":"https://ocw.mit.edu/courses/8-02sc-physics-ii-electricity-and-magnetism-fall-2012/","why":"Detailed derivations."},
                {"type":"practice","title":"E&M problems (OCW)","url":"https://ocw.mit.edu/courses/8-02sc-physics-ii-electricity-and-magnetism-fall-2012/pages/problem-solving-help/problem-set/","why":"Practice with solutions."}
            ],
            "practice": [
                {"prompt":"Compute the capacitance of a parallel-plate capacitor with area A and separation d in vacuum."},
                {"prompt":"Use Faraday’s law to find induced EMF for a loop in a changing magnetic field."}
            ],
            "ideas": ["C=εA/d for parallel plates","Lenz’s law & induction","Field energy storage in C/L"]
        },
        # --- Humanities & Social Sciences ---

    "writing.essay": {
        "keywords": ["essay","reflection","thesis","argument","outline","citation","mla","apa","chicago","literature review"],
        "resources": [
            {"type":"notes","title":"Purdue OWL — Academic Writing","url":"https://owl.purdue.edu/owl/general_writing/academic_writing/index.html","why":"The gold-standard for structure, clarity, and style."},
            {"type":"notes","title":"UNC Writing Center — Handouts","url":"https://writingcenter.unc.edu/handouts/","why":"Concrete guidance with examples (thesis, paragraphs, transitions)."},
            {"type":"tool","title":"Zotero — Reference Manager","url":"https://www.zotero.org/","why":"Collect sources and generate citations the clean way."}
        ],
        "practice": [
            {"prompt":"Write a 1-paragraph thesis + 3 bullet arguments for your topic. Stress test each with a counterexample."},
            {"prompt":"Reverse outline your draft: one sentence per paragraph; check logical flow and evidence support."}
        ],
        "ideas":["Plan → Draft → Revise loop","One claim per paragraph","Evidence → Analysis → Link-back"]
    },

    "literature.analysis": {
        "keywords": ["close reading","symbolism","motif","narrative voice","poetry analysis","novel analysis","theme","tone"],
        "resources": [
            {"type":"notes","title":"LitCharts — Literary Devices","url":"https://www.litcharts.com/literary-devices-and-terms","why":"Quick definitions + examples for close reading."},
            {"type":"notes","title":"SparkNotes — Literature Guides","url":"https://www.sparknotes.com/lit/","why":"Plot/theme refreshers (don’t cite; use to orient)."},
            {"type":"source","title":"Project Gutenberg — Free Books","url":"https://www.gutenberg.org/","why":"Primary texts for classics without paywalls."}
        ],
        "practice": [
            {"prompt":"Pick one passage (≤150 words). Identify device (metaphor/irony/etc.) and explain its effect on theme."},
            {"prompt":"Map character arcs: 3 turning points and how each shifts the central conflict."}
        ],
        "ideas":["Quote → Paraphrase → Analyze sandwich","Form supports meaning","Author’s choice ≠ narrator’s belief"]
    },

    "history.modern": {
        "keywords": ["primary source","historiography","revolution","industrialization","cold war","treaty","empire","colonial","source analysis"],
        "resources": [
            {"type":"source","title":"Internet History Sourcebooks","url":"https://sourcebooks.fordham.edu/","why":"Curated primary sources by topic/era."},
            {"type":"notes","title":"BBC Bitesize — History","url":"https://www.bbc.co.uk/bitesize/subjects/zk26n39","why":"Concise primers for context building."},
            {"type":"method","title":"SHEG — Reading Like a Historian","url":"https://sheg.stanford.edu/","why":"Evidence evaluation, sourcing, corroboration."}
        ],
        "practice": [
            {"prompt":"SOURCING: Who wrote this, when, for whom, and why? Write a 5-sentence source critique."},
            {"prompt":"Causation chain: list 3 causes → 3 effects for your event; label short- vs long-term."}
        ],
        "ideas":["Context > Quote mining","Corroborate across sources","Continuity/change over time"]
    },

    "philosophy.ethics": {
        "keywords": ["utilitarianism","deontology","virtue ethics","consequentialism","trolley problem","normative","metaethics","applied ethics"],
        "resources": [
            {"type":"reference","title":"Stanford Encyclopedia of Philosophy","url":"https://plato.stanford.edu/","why":"Authoritative, citable entries with bibliographies."},
            {"type":"reference","title":"Internet Encyclopedia of Philosophy","url":"https://iep.utm.edu/","why":"Readable overviews to get bearings fast."}
        ],
        "practice": [
            {"prompt":"State the dilemma in 2 sentences; outline how a utilitarian vs a deontologist would decide (1 paragraph each)."},
            {"prompt":"Find one objection to your position and steelman it (strongest fair version)."}
        ],
        "ideas":["Separate facts from values","Principle test vs outcomes test","Steelman before you rebut"]
    },

    "law.contracts": {
        "keywords": ["offer","acceptance","consideration","breach","damages","UCC","common law","parol evidence","contract formation","promissory estoppel"],
        "resources": [
            {"type":"reference","title":"Cornell LII — Contract Law","url":"https://www.law.cornell.edu/wex/contract","why":"Clear, free summaries with links to cases."},
            {"type":"guide","title":"IRAC Method Overview","url":"https://www.law.cornell.edu/wex/irac","why":"Issue-Rule-Application-Conclusion writing scaffold."}
        ],
        "practice": [
            {"prompt":"IRAC a mini-fact pattern: identify issue(s), state rules briefly, apply to facts, conclude."},
            {"prompt":"Draft a one-paragraph contract clause (termination or confidentiality) and note ambiguity risks."}
        ],
        "ideas":["Elements > Labels","Facts drive application","Ambiguity is the enemy"]
    },

    # --- Arts & Creative ---

    "art.analysis": {
        "keywords": ["visual analysis","composition","color theory","iconography","renaissance","modernism","impressionism","formal analysis"],
        "resources": [
            {"type":"notes","title":"Smarthistory — Art History","url":"https://smarthistory.org/","why":"Short expert essays with images."},
            {"type":"gallery","title":"Google Arts & Culture","url":"https://artsandculture.google.com/","why":"High-res works, timelines, themes."}
        ],
        "practice": [
            {"prompt":"Formal analysis: subject, composition, light/color, technique — 200 words on a chosen piece."},
            {"prompt":"Compare two works: one similarity, one key difference, and what each choice achieves."}
        ],
        "ideas":["Describe before interpret","Form → function → context","Avoid biography dumps"]
    },

    "music.theory": {
        "keywords": ["intervals","chords","harmony","voice leading","roman numerals","cadence","scale degrees","counterpoint"],
        "resources": [
            {"type":"lesson","title":"musictheory.net — Lessons","url":"https://www.musictheory.net/lessons","why":"Interactive basics, fast to review."},
            {"type":"exercise","title":"Teoria — Exercises","url":"https://www.teoria.com/en/exercises/","why":"Ear-training and theory drills."},
            {"type":"library","title":"IMSLP — Sheet Music","url":"https://imslp.org/","why":"Practice with public domain scores."}
        ],
        "practice": [
            {"prompt":"Roman-numeral analyze a 4-bar progression in a major key; identify cadence type."},
            {"prompt":"Write a ii–V–I in two keys and voice-lead with minimal motion."}
        ],
        "ideas":["Function over shape","Voice-leading > leaps","Hear it, don’t just see it"]
    },

    # --- Business, Econ, Psych ---

    "business.case": {
        "keywords": ["case study","swot","porter five forces","value proposition","unit economics","market sizing","go to market"],
        "resources": [
            {"type":"notes","title":"Strategy — Porter’s Five Forces (Investopedia)","url":"https://www.investopedia.com/terms/p/porter.asp","why":"Quick refresher on competitive analysis."},
            {"type":"notes","title":"Value Proposition Canvas (Strategyzer)","url":"https://www.strategyzer.com/canvas/value-proposition-canvas","why":"Map pains/gains to product features."}
        ],
        "practice": [
            {"prompt":"One-pager: problem, segment, solution, moat, GTM; include 3 key risks."},
            {"prompt":"Market sizing: top-down and bottom-up estimates with assumptions shown."}
        ],
        "ideas":["Assumptions → Numbers → Sensitivity","Differentiate or die","Customer > competitor obsession"]
    },

    "economics.micro": {
        "keywords": ["supply demand","elasticity","opportunity cost","marginal","consumer surplus","producer surplus","equilibrium"],
        "resources": [
            {"type":"video","title":"MRU — Principles of Microeconomics","url":"https://mru.org/courses/principles-economics-microeconomics","why":"Clear, short video lessons."},
            {"type":"course","title":"Khan Academy — Microeconomics","url":"https://www.khanacademy.org/economics-finance-domain/microeconomics","why":"Practice problems with hints."}
        ],
        "practice": [
            {"prompt":"Sketch a demand shift (income ↑) and compute new equilibrium; discuss surplus changes."},
            {"prompt":"Explain price elasticity with a real product; estimate and defend your guess."}
        ],
        "ideas":["Think at the margin","Incentives matter","Beware ceteris paribus leaks"]
    },

    "psychology.methods": {
        "keywords": ["experiment","operationalization","validity","reliability","p-value","effect size","ethics","irb","survey","random assignment"],
        "resources": [
            {"type":"notes","title":"APA — Research Methods","url":"https://www.apa.org/education-career/undergrad/careers/research-methods","why":"Core concepts and terminology."},
            {"type":"notes","title":"SimplyPsychology — Research Methods","url":"https://www.simplypsychology.org/research-methods.html","why":"Digestible summaries with examples."}
        ],
        "practice": [
            {"prompt":"Design a simple experiment: hypothesis, variables, operational definitions, and ethics note."},
            {"prompt":"Identify two threats to validity in a given study and how to mitigate them."}
        ],
        "ideas":["Measure what matters","Validity > significance","Pre-register where possible"]
    },

    # --- General Academic Skills ---

    "presentation.skills": {
        "keywords": ["presentation","slides","public speaking","deck","pitch","talk","poster","visual communication"],
        "resources": [
            {"type":"guide","title":"Garr Reynolds — Presentation Zen Principles","url":"https://www.presentationzen.com/","why":"Design simplicity and clarity."},
            {"type":"notes","title":"Duarte — Slide Design Basics","url":"https://www.duarte.com/presentation-skills-resources/","why":"Practical layout/story tips."}
        ],
        "practice": [
            {"prompt":"Storyboard 6 slides: hook, problem, insight, solution, proof, next steps."},
            {"prompt":"Rebuild a dense slide with 1 idea per slide and a clear visual hierarchy."}
        ],
        "ideas":["One idea per slide","Show, don’t tell","Rehearse transitions, not just content"]
    },

    "study.skills": {
        "keywords": ["pomodoro","spaced repetition","anki","active recall","timeboxing","procrastination","focus"],
        "resources": [
            {"type":"guide","title":"Cornell Note-Taking System","url":"https://lsc.cornell.edu/how-to-study/taking-notes/cornell-note-taking-system/","why":"Structured notes that aid recall."},
            {"type":"guide","title":"Pomodoro Technique","url":"https://francescocirillo.com/pages/pomodoro-technique","why":"Simple cadence to break resistance."},
            {"type":"tool","title":"Anki (Spaced Repetition)","url":"https://apps.ankiweb.net/","why":"Make facts stick with optimal intervals."}
        ],
        "practice": [
            {"prompt":"Plan 2×25-minute pomodoros for your hardest task; write the exact sub-steps."},
            {"prompt":"Make 10 active-recall flashcards from today’s reading (one fact per card)."}
        ],
        "ideas":["Recall > re-read","Short sprints beat marathons","Reduce friction to start"]
    },
    "finnish.conversation1": {
        "keywords": ["small talk", "daily activities", "present tense practice"],
        "resources": [
            {"type":"practice","title":"Duolingo — Finnish Basics Review","url":"https://www.duolingo.com/course/fi/en/Learn-Finnish"}
        ],
        "practice": [
            {"prompt":"Roleplay: Meet a new friend and ask about their day."},
            {"prompt":"Describe what you usually do on weekdays."}
        ],
        "ideas": [
            "Small talk in Finnish often uses simple questions: Mitä kuuluu?",
            "Daily routines reinforce verb conjugations in present tense."
        ]
    },

    "finnish.conversation2": {
        "keywords": ["opinions", "preferences", "hobbies", "comparisons"],
        "resources": [
            {"type":"notes","title":"Uusi Kielemme — Comparative forms","url":"https://uusikielemme.fi/finnish-grammar/adjectives/comparative-and-superlative"}
        ],
        "practice": [
            {"prompt":"Say what your favorite hobby is and why."},
            {"prompt":"Compare two things: kahvi on parempaa kuin tee."}
        ],
        "ideas": [
            "Opinions often use the partitive: Tykkään kahvista.",
            "Comparisons use ‘kuin’ (better than)."
        ]
    },

    "finnish.work1": {
        "keywords": ["workplace vocabulary", "professions", "email writing"],
        "resources": [
            {"type":"notes","title":"Uusi Kielemme — Professions","url":"https://uusikielemme.fi/finnish-vocabulary/lists/people/professions"}
        ],
        "practice": [
            {"prompt":"Write a short email introducing yourself for a job."},
            {"prompt":"Describe your profession and workplace in Finnish."}
        ],
        "ideas": [
            "Finnish workplace culture values formality in introductions.",
            "Professions use nominative case when describing roles."
        ]
    },

    "finnish.work2": {
        "keywords": ["meetings", "formal language", "requests"],
        "resources": [
            {"type":"notes","title":"Uusi Kielemme — Polite Expressions","url":"https://uusikielemme.fi/finnish-grammar/miscellaneous/polite-requests"}
        ],
        "practice": [
            {"prompt":"Make a polite request using voisitteko …?"},
            {"prompt":"Roleplay a short workplace meeting dialogue."}
        ],
        "ideas": [
            "Formal Finnish uses plural forms for politeness.",
            "Meetings often use modal verbs for requests."
        ]
    },

    "finnish.work3": {
        "keywords": ["job applications", "CV vocabulary", "interviews"],
        "resources": [
            {"type":"notes","title":"Uusi Kielemme — Applying for Work","url":"https://uusikielemme.fi/finnish-vocabulary/lists/work/applying-for-work"}
        ],
        "practice": [
            {"prompt":"Write 5 sentences for your CV in Finnish."},
            {"prompt":"Practice answering ‘Miksi haluat tämän työn?’."}
        ],
        "ideas": [
            "Finnish CVs are concise and factual.",
            "Interview questions test both language and cultural fit."
        ]
    },
    "finnish.I": {
        "keywords": [
            "greetings", "introduction", "personal details", "questions and answers",
            "numbers", "alphabet", "countries", "languages", "nationalities",
            "pronunciation", "verb type 1", "present tense", "genitive case",
            "at the cafe", "shopping in Finland"
        ],
        "resources": [
            {"type":"notes","title":"Uusi Kielemme — Learn Finnish","url":"https://uusikielemme.fi/"},
            {"type":"notes","title":"FinnishPod101 — Introduction","url":"https://www.finnishpod101.com/"},
            {"type":"practice","title":"Duolingo — Finnish Course","url":"https://www.duolingo.com/course/fi/en/Learn-Finnish"},
            {"type":"practice","title":"Memrise — Finnish 1","url":"https://app.memrise.com/course/2021577/learn-finnish-1/"}
        ],
        "practice": [
            {"prompt":"Introduce yourself in Finnish: name, nationality, and one hobby."},
            {"prompt":"Write a short dialogue ordering coffee in a café."},
            {"prompt":"Practice counting from 1 to 20 and spelling your name aloud."}
        ],
        "ideas": [
            "Finnish has 15 cases; genitive indicates possession.",
            "Verb type 1: endings in -a/-ä (puhua → minä puhun).",
            "The alphabet includes ä and ö, pronounced distinctly.",
            "Word stress is always on the first syllable.",
            "Present tense is used for both current and general actions."
        ]
    },

    "finnish.II": {
        "keywords": ["family", "time expressions", "verb type 2", "questions", "ordinal numbers"],
        "resources": [
            {"type":"notes","title":"Uusi Kielemme — Verb Types","url":"https://uusikielemme.fi/finnish-grammar/verbs/verbtypes"},
            {"type":"practice","title":"Memrise — Finnish 2","url":"https://app.memrise.com/course/2021578/learn-finnish-2/"}
        ],
        "practice": [
            {"prompt":"Describe your family in 3–4 sentences."},
            {"prompt":"Ask and answer questions about the time (Kello on …)."},
            {"prompt":"Conjugate three verb type 2 verbs in present tense."}
        ],
        "ideas": [
            "Verb type 2 verbs end in -da/-dä (syödä → syön).",
            "Ordinal numbers used for dates and order (ensimmäinen, toinen).",
            "Time expressions use partitive and genitive cases."
        ]
    },

    "finnish.III": {
        "keywords": ["weather", "directions", "transport", "verb type 3", "past tense"],
        "resources": [
            {"type":"notes","title":"Uusi Kielemme — Past Tense","url":"https://uusikielemme.fi/finnish-grammar/verbs/tense/past-tense"},
            {"type":"practice","title":"Memrise — Finnish 3","url":"https://app.memrise.com/course/2021579/learn-finnish-3/"}
        ],
        "practice": [
            {"prompt":"Write 3 sentences about today’s weather."},
            {"prompt":"Give directions from your house to the supermarket."},
            {"prompt":"Conjugate ‘mennä’ in past tense (minä menin, sinä menit …)."}
        ],
        "ideas": [
            "Verb type 3: stems end in -la, -na, -ra, -sta (mennä, tulla).",
            "Past tense adds -i- before endings.",
            "Weather phrases often use impersonal forms (Sataa vettä)."
        ]
    },

    "finnish.IV": {
        "keywords": ["future expressions", "partitive case", "shopping", "food vocabulary"],
        "resources": [
            {"type":"notes","title":"Uusi Kielemme — Partitive Case","url":"https://uusikielemme.fi/finnish-grammar/cases/partitive-case"},
            {"type":"practice","title":"Memrise — Finnish 4","url":"https://app.memrise.com/course/2021580/learn-finnish-4/"}
        ],
        "practice": [
            {"prompt":"Order a meal at a restaurant using partitive case."},
            {"prompt":"Make a shopping list with 10 food items."},
            {"prompt":"Write 3 sentences about what you will do tomorrow using tuleva expressions."}
        ],
        "ideas": [
            "Finnish has no true future tense; present is used with context.",
            "Partitive case expresses incomplete objects or quantity (juon vettä).",
            "Food vocabulary is essential for daily interaction."
        ]
    },
    "programming.intro": {
        "keywords": [
            "IDLE", "Python", "Datatypes", "low level", "integers", "floats", "strings",
            "rounding", "syntax errors", "operations", "addition", "subtraction",
            "multiplication", "division", "integer division", "exponents", "modulus",
            "unary plus minus", "variables", "dynamic typing", "input", "output",
            "type conversion"
        ],
        "resources": [
            {"type":"video","title":"Echo360 — Python basics, datatypes","url":"https://echo360.org.uk/media/6340dd94-983a-41c3-9585-b3f940b927a4/public"},
            {"type":"video","title":"Echo360 — Operations, variables","url":"https://echo360.org.uk/media/6554e7be-9576-4216-a8a5-a2284e30b981/public"},
            {"type":"video","title":"Echo360 — Input, output, type conversion","url":"https://echo360.org.uk/media/43a93c25-0e21-4a91-b75c-b4c42757aedc/public"},
            {"type":"notes","title":"W3Schools — Python Data Types","url":"https://www.w3schools.com/python/python_datatypes.asp"},
            {"type":"notes","title":"RealPython — Python Numbers","url":"https://realpython.com/python-numbers/"},
            {"type":"practice","title":"Exercism — Python Basics","url":"https://exercism.org/tracks/python/exercises"}
        ],
        "practice": [
            {"prompt":"Write a program that asks the user for two numbers and prints their sum, difference, product, and quotient."},
            {"prompt":"Take an integer input and print its square, cube, and modulus when divided by 5."},
            {"prompt":"Ask for a float input, round it to 2 decimals, and print the result."}
        ],
        "ideas": [
            "Python supports multiple data types: int, float, str.",
            "Dynamic typing: variables don’t need explicit type declarations.",
            "Division vs integer division: / vs //.",
            "Type conversion is necessary when mixing input() with numbers.",
            "Syntax errors stop code from running; runtime errors happen while running."
        ]
    },

    "programming.strings": {
        "keywords": [
            "commenting code", "strings", "modify print", "convert numbers",
            "f-strings", "string operations", "concatenation", "slicing"
        ],
        "resources": [
            {"type":"video","title":"Echo360 — Strings basics","url":"https://echo360.org.uk/media/87308e24-b9d9-4c66-80f5-f2f3912e31d0/public"},
            {"type":"video","title":"Echo360 — Print & string formatting","url":"https://echo360.org.uk/media/9cfd8f9c-d89f-408c-802b-29ed0490428f/public"},
            {"type":"video","title":"Echo360 — More string formatting","url":"https://echo360.org.uk/media/34ecef0b-c15a-46d1-a762-6cf7cf93b194/public"},
            {"type":"video","title":"Echo360 — f-strings and printing","url":"https://echo360.org.uk/media/2090a733-0626-4d77-a201-ced15702c4ee/public"},
            {"type":"video","title":"Echo360 — String operations","url":"https://echo360.org.uk/media/4a0243b2-6bca-4310-8cae-76ed5f3bc471/public"},
            {"type":"video","title":"Echo360 — More on strings","url":"https://echo360.org.uk/media/7fe8b8e2-e1c0-4447-b41c-5eeaa148c543/public"},
            {"type":"notes","title":"W3Schools — Python Strings","url":"https://www.w3schools.com/python/python_strings.asp"},
            {"type":"practice","title":"HackerRank — Python String Split and Join","url":"https://www.hackerrank.com/challenges/python-string-split-and-join/problem"}
        ],
        "practice": [
            {"prompt":"Write a program that takes a user’s name and prints a greeting using f-strings."},
            {"prompt":"Take a string input and print it in uppercase, lowercase, and reversed."},
            {"prompt":"Concatenate two strings and print the length of the result."}
        ],
        "ideas": [
            "Strings are immutable in Python.",
            "Use f-strings for clean, readable formatting.",
            "The print() function can be customized with sep and end parameters.",
            "String slicing lets you extract substrings: s[start:end].",
            "Type conversion allows concatenating numbers with strings."
        ]
    },

    "programming.ai": {
        "keywords": ["AI", "artificial intelligence", "teacher", "AI as a teacher"],
        "resources": [
            {"type":"notes","title":"IBM — What is Artificial Intelligence?","url":"https://www.ibm.com/topics/artificial-intelligence"},
            {"type":"notes","title":"W3Schools — AI Introduction","url":"https://www.w3schools.com/ai/"},
            {"type":"practice","title":"Kaggle — Intro to AI & Machine Learning","url":"https://www.kaggle.com/learn/intro-to-machine-learning"}
        ],
        "practice": [
            {"prompt":"Research how AI can support learning programming and write a short reflection."},
            {"prompt":"Compare a solution you write in Python to one generated by an AI assistant."}
        ],
        "ideas": [
            "AI can act as a tutor by providing instant feedback.",
            "AI systems rely on models that may simplify reality.",
            "Human oversight is important to ensure accuracy and ethics."
        ]
    },

    "programming.conditionals": {
        "keywords": [
            "bool", "boolean", "true", "false", "comparison", "in",
            "boolean operators", "short circuiting",
            "if", "elif", "else", "condition", "indentation", "block of code",
            "match case", "numbers", "strings", "boolean values"
        ],
        "resources": [
            {"type":"video","title":"Echo360 — Boolean basics","url":"https://echo360.org.uk/media/a3c066ac-dcad-4d2e-a9e9-22b85fc5851d/public"},
            {"type":"video","title":"Echo360 — Boolean operators","url":"https://echo360.org.uk/media/f378eb90-c264-462c-b970-494a7b4df8a3/public"},
            {"type":"video","title":"Echo360 — If statements","url":"https://echo360.org.uk/media/3e26864e-dab7-4de4-bad3-ef7ec0d793ab/public"},
            {"type":"video","title":"Echo360 — Elif & Else","url":"https://echo360.org.uk/media/c0e691de-db76-46ca-b0f0-448b4e1071a1/public"},
            {"type":"video","title":"Echo360 — Match-case","url":"https://echo360.org.uk/media/af54a095-b8d3-4405-baee-72a5a3be9038/public"},
            {"type":"notes","title":"W3Schools — Python Conditions","url":"https://www.w3schools.com/python/python_conditions.asp"},
            {"type":"practice","title":"PracticePython — Exercise 2 (Odd or Even)","url":"https://www.practicepython.org/exercise/2014/02/05/02-odd-or-even.html"}
        ],
        "practice": [
            {"prompt":"Write a program that checks if a number is even or odd using if-else."},
            {"prompt":"Create a program that prints 'Hello' if a variable is True, otherwise 'Goodbye'."},
            {"prompt":"Use match-case to classify input as 'yes', 'no', or 'unknown'."}
        ],
        "ideas": [
            "Booleans: True/False, 1/0.",
            "Comparison operators: ==, !=, <, >, <=, >=.",
            "Boolean operators short-circuit (and/or).",
            "Indentation defines scope in Python.",
            "match-case works like switch in other languages."
        ]
    },
    "programming.loops": {
        "keywords": [
            "while loop", "for loop", "loop", "iteration", "in keyword",
            "range()", "break", "continue", "nested loops"
        ],
        "resources": [
            {"type":"video","title":"Echo360 — While loops","url":"https://echo360.org.uk/media/1e2f3f4c-1f0e-4d6b-9a7e-3c8e2f4b5c6d/public"},
            {"type":"video","title":"Echo360 — For loops","url":"https://echo360.org.uk/media/2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e/public"},
            {"type":"video","title":"Echo360 — Nested loops & loop control","url":"https://echo360.org.uk/media/3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f/public"},
            {"type":"notes","title":"W3Schools — Python Loops","url":"https://www.w3schools.com/python/python_loops.asp"},
            {"type":"practice","title":"HackerRank — Python Loops","url":"https://www.hackerrank.com/challenges/python-loops/problem"}
        ],
        "practice": [
            {"prompt":"Write a while loop that prints numbers from 1 to 10."},
            {"prompt":"Create a for loop that iterates over a list of fruits and prints each one."},
            {"prompt":"Use nested loops to print a multiplication table (1–5)." }
        ],
        "ideas": [
            "while loops run until a condition is False.",
            "for loops iterate over sequences (lists, strings, ranges).",
            "range(start, stop, step) generates a sequence of numbers.",
            "break exits the loop; continue skips to the next iteration.",
            "Nested loops are useful for multi-dimensional data."
        ]
    },
    "programming.functions": {
        "keywords": [
            "function", "def", "parameter", "argument", "return",
            "docstring", "scope", "local variable", "global variable",
            "lambda", "list comprehension"
        ],
        "resources": [
            {"type":"video","title":"Echo360 — Functions basics","url":"https://echo360.org.uk/media/4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a/public"},
            {"type":"video","title":"Echo360 — Parameters & return","url":"https://echo360.org.uk/media/5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b/public"},
            {"type":"video","title":"Echo360 — Scope & docstrings","url":"https://echo360.org.uk/media/6f7a8b9c-0d1e-2f3a-4b5c-6d7e8f9a0b1c/public"},
            {"type":"video","title":"Echo360 — Lambda & list comprehensions","url":"https://echo360.org.uk/media/7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d/public"},
            {"type":"notes","title":"W3Schools — Python Functions","url":"https://www.w3schools.com/python/python_functions.asp"},
            {"type":"practice","title":"Exercism — Python Functions","url":"https://exercism.org/tracks/python/exercises/leap"}
        ],
        "practice": [
            {"prompt":"Define a function that takes two numbers and returns their sum."},
            {"prompt":"Write a function that checks if a string is a palindrome."},
            {"prompt":"Create a lambda function that squares a number and use it in a list comprehension to square a list of numbers."}
        ],
        "ideas": [
            "Functions encapsulate reusable code blocks.",
            "Parameters are placeholders; arguments are actual values passed in.",
            "Use return to send results back from functions.",
            "Docstrings describe function purpose and usage.",
            "Local variables exist only within the function scope.",
            "Lambda functions are anonymous, single-expression functions.",
        ]
    },  
        "cs.algorithms": {
        "keywords": ["algorithm","sorting","binary search","graph","dijkstra","complexity","big-o"],
        "resources": [
            {"type":"notes","title":"VisuAlgo","url":"https://visualgo.net/en","why":"Animated algorithm walkthroughs."},
            {"type":"course","title":"MIT OCW 6.006 — Intro to Algorithms","url":"https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/","why":"Classic lecture notes + problems."}
        ],
        "practice": [
            {"prompt":"Implement binary search in your language of choice; test with unsorted list (should fail)."},
            {"prompt":"Trace Dijkstra’s algorithm by hand on a 6-node weighted graph."}
        ],
        "ideas":["Time vs space tradeoffs","Recursive vs iterative","Data structure choice = performance"]
    },

    "bio.genetics": {
        "keywords": ["dna","rna","gene","chromosome","allele","inheritance","genetics","punnett","mutation","sequencing"],
        "resources": [
            {"type":"notes","title":"Khan Academy — Heredity and Genetics","url":"https://www.khanacademy.org/science/biology/heredity","why":"Clear basics with practice problems."},
            {"type":"reference","title":"NCBI Genetics Home Reference","url":"https://ghr.nlm.nih.gov/","why":"Authoritative resource on genes and conditions."}
        ],
        "practice": [
            {"prompt":"Draw a Punnett square for Aa x Aa. What’s the probability of a homozygous recessive?"},
            {"prompt":"Explain how a point mutation can alter protein structure."}
        ],
        "ideas":["Central Dogma: DNA→RNA→Protein","Dominant ≠ common","Mutations drive diversity & disease"]
    },

    "chem.organic": {
        "keywords": ["alkane","alkene","alcohol","functional group","reaction mechanism","nucleophile","electrophile"],
        "resources": [
            {"type":"notes","title":"MasterOrganicChemistry","url":"https://www.masterorganicchemistry.com/","why":"Reaction guides with visuals."},
            {"type":"notes","title":"Organic Chemistry Portal","url":"https://www.organic-chemistry.org/","why":"Reaction summaries, named reactions."}
        ],
        "practice": [
            {"prompt":"Draw the mechanism of SN1 vs SN2 substitution for 2-bromopropane."},
            {"prompt":"Identify functional groups in caffeine molecule."}
        ],
        "ideas":["Mechanism > memorization","Electron flow with arrows","Structure drives reactivity"]
    },

    "astro.stars": {
        "keywords": ["stellar","nebula","supernova","main sequence","white dwarf","black hole","fusion"],
        "resources": [
            {"type":"notes","title":"NASA Imagine the Universe — Stars","url":"https://imagine.gsfc.nasa.gov/science/objects/stars1.html","why":"Accessible explanations from NASA."},
            {"type":"course","title":"OpenStax Astronomy","url":"https://openstax.org/books/astronomy/pages/1-introduction","why":"Free, comprehensive textbook."}
        ],
        "practice": [
            {"prompt":"Sketch the Hertzsprung–Russell diagram and plot Sun, Betelgeuse, Sirius."},
            {"prompt":"Explain what happens when a star exhausts hydrogen in its core."}
        ],
        "ideas":["Mass decides fate","Fusion = energy","Life cycles are billions of years long"]
    },
    "geo.climate": {
        "keywords": ["climate change","greenhouse gas","carbon cycle","mitigation","adaptation","fossil fuel","renewable energy"],
        "resources": [
            {"type":"notes","title":"NASA Climate Change & Global Warming","url":"https://climate.nasa.gov/","why":"Data-driven insights and visualizations."},
            {"type":"course","title":"Khan Academy — Climate Change","url":"https://www.khanacademy.org/science/biology/ecology/biogeochemical-cycles/a/climate-change-overview","why":"Clear explanations with practice."}
        ],
        "practice": [
            {"prompt":"Describe the greenhouse effect in 3 sentences."},
            {"prompt":"List 3 mitigation strategies and their pros/cons."}
        ],
        "ideas":["Human activity drives recent change","Feedback loops amplify effects","Local actions have global impact"]
    },
    "med.microbiology": {
        "keywords": ["bacteria","virus","fungi","parasite","immune system","antibiotic","vaccine","pathogen"],
        "resources": [
            {"type":"notes","title":"Microbiology Society — Microbes","url":"https://microbiologysociety.org/why-microbiology-matters/what-is-microbiology.html","why":"Foundational concepts and applications."},
            {"type":"course","title":"Coursera — Medical Microbiology","url":"https://www.coursera.org/learn/medical-microbiology","why":"Comprehensive course with quizzes."}
        ],
        "practice": [
            {"prompt":"Compare and contrast bacteria vs viruses in structure and replication."},
            {"prompt":"Explain how vaccines stimulate the immune system."}
        ],
        "ideas":["Microbes are everywhere","Not all microbes are harmful","Antibiotic resistance is a growing threat"]
    },
    "business.analytics": {
        "keywords": ["business analytics", "data analysis", "visualization", "decision making"],
        "resources": [
            {"type":"notes","title":"Harvard Business Review — Business Analytics Basics","url":"https://hbr.org/topic/business-analytics"},
            {"type":"notes","title":"Kaggle — Datasets for Analytics","url":"https://www.kaggle.com/datasets"},
            {"type":"practice","title":"Coursera — Business Analytics Specialization","url":"https://www.coursera.org/specializations/business-analytics"}
        ],
        "practice": [
            {"prompt":"Analyze a dataset (sales, marketing, or finance) and summarize business insights in 3 bullet points."},
            {"prompt":"Create a visualization (bar chart, line chart) from sales data to identify trends."}
        ],
        "ideas": [
            "Business analytics bridges raw data with decision-making.",
            "Visualization is key to communicating insights.",
            "Common tools: Excel, Python (pandas, matplotlib), Power BI, Tableau."
        ]
    },

    "business.applied_international": {
        "keywords": ["applied international business", "global markets", "trade", "cross-cultural"],
        "resources": [
            {"type":"notes","title":"OECD — International Business Reports","url":"https://www.oecd.org/trade/"},
            {"type":"notes","title":"World Bank — Doing Business","url":"https://www.worldbank.org/en/programs/business-enabling-environment"}
        ],
        "practice": [
            {"prompt":"Compare two countries’ approaches to trade policy and summarize their business environments."},
            {"prompt":"Identify risks and opportunities for a company entering a foreign market."}
        ],
        "ideas": [
            "Cross-cultural differences influence negotiations.",
            "Global trade policies impact business strategies.",
            "International supply chains require resilience planning."
        ]
    },

    "business.big_data": {
        "keywords": ["big data", "data science", "machine learning", "cloud analytics"],
        "resources": [
            {"type":"video","title":"What is Big Data? — IBM","url":"https://www.youtube.com/watch?v=o9UjzNgA_OI"},
            {"type":"notes","title":"Big Data Basics — AWS","url":"https://aws.amazon.com/big-data/datalakes-and-analytics/"},
            {"type":"practice","title":"Google Cloud Big Data Tutorials","url":"https://cloud.google.com/big-data"}
        ],
        "practice": [
            {"prompt":"Explain the 3Vs of big data (volume, velocity, variety) with examples."},
            {"prompt":"Run a word frequency analysis on a large text dataset."}
        ],
        "ideas": [
            "Big data enables predictive analytics.",
            "Cloud platforms provide scalable solutions.",
            "Machine learning models rely on large datasets."
        ]
    },

    "business.market_analysis": {
        "keywords": ["market analysis", "models", "competition", "strategy"],
        "resources": [
            {"type":"notes","title":"Porter’s Five Forces — Investopedia","url":"https://www.investopedia.com/terms/p/porter.asp"},
            {"type":"notes","title":"SWOT Analysis Guide","url":"https://www.businessnewsdaily.com/4245-swot-analysis.html"},
            {"type":"practice","title":"Market Analysis Case Studies","url":"https://hbr.org/topic/market-analysis"}
        ],
        "practice": [
            {"prompt":"Conduct a SWOT analysis for a startup entering the EV market."},
            {"prompt":"Apply Porter’s Five Forces to analyze the coffee industry."}
        ],
        "ideas": [
            "Market models help evaluate competition.",
            "SWOT and Five Forces provide structured frameworks.",
            "Trends and customer insights drive product strategy."
        ]
    },
    "lut.studies": {
        "keywords": ["bachelor", "master", "doctoral", "graduation", "exchange students", "open university", "orientation", "summer studies", "tutoring"],
        "resources": [
            {"type":"notes","title":"LUT University — Studies Overview","url":"https://www.lut.fi/en/studies"},
            {"type":"notes","title":"LUT Exchange Programs","url":"https://www.lut.fi/en/exchange-students"}
        ],
        "practice": [
            {"prompt":"List three key differences between LUT bachelor’s and master’s programs."},
            {"prompt":"Prepare a mock orientation guide for a new international student."}
        ],
        "ideas": [
            "LUT offers a wide range of international programs.",
            "Exchange opportunities broaden global perspectives.",
            "Tutoring and summer schools support integration."
        ]
    },

    "lut.platforms": {
        "keywords": ["sisu", "moodle", "timeedit", "outlook", "study guidance"],
        "resources": [
            {"type":"notes","title":"Sisu — LUT","url":"https://sisu.lut.fi"},
            {"type":"notes","title":"Moodle — LUT","url":"https://moodle.lut.fi"},
            {"type":"notes","title":"TimeEdit — LUT","url":"https://cloud.timeedit.net"},
            {"type":"notes","title":"Outlook — LUT","url":"https://outlook.office365.com"}
        ],
        "practice": [
            {"prompt":"Log into Sisu and check your registered courses."},
            {"prompt":"Navigate Moodle and locate assignment deadlines."}
        ],
        "ideas": [
            "Sisu manages study plans and course registration.",
            "Moodle is the main course content platform.",
            "TimeEdit handles scheduling and timetables."
        ]
    },

    "lut.housing": {
        "keywords": ["housing", "LOAS", "student housing", "accommodation"],
        "resources": [
            {"type":"notes","title":"LOAS — Lappeenranta Housing Foundation","url":"https://www.loas.fi/en"}
        ],
        "practice": [
            {"prompt":"Find three types of accommodation available through LOAS."},
            {"prompt":"Compare student housing vs private rental options in Lappeenranta."}
        ],
        "ideas": [
            "LOAS provides affordable student housing.",
            "Accommodation options vary from shared flats to studios.",
            "Location and budget guide housing choices."
        ]
    },
        "sociology.intro": {
        "keywords": ["society","culture","norms","values","institutions","socialization","stratification"],
        "resources": [
            {"type":"notes","title":"Khan Academy — Sociology","url":"https://www.khanacademy.org/test-prep/mcat/society-and-culture","why":"Intro with MCAT-aligned examples."},
            {"type":"notes","title":"OpenStax Sociology","url":"https://openstax.org/books/introduction-sociology-3e","why":"Free textbook with examples."}
        ],
        "practice": [
            {"prompt":"Define a social norm in your community. What sanctions (positive/negative) enforce it?"},
            {"prompt":"Explain stratification with an example of class, race, or gender."}
        ],
        "ideas":["Society shapes individual","Institutions maintain order","Norms are invisible until broken"]
    },

    "politics.comparative": {
        "keywords": ["democracy","authoritarian","parliament","regime","state","government","policy","election"],
        "resources": [
            {"type":"notes","title":"Comparative Politics Resource Guide","url":"https://guides.library.cornell.edu/comparativepolitics","why":"Overview with key theories and cases."},
            {"type":"data","title":"Varieties of Democracy (V-Dem)","url":"https://v-dem.net/","why":"Huge dataset on democracy worldwide."}
        ],
        "practice": [
            {"prompt":"Compare presidential vs parliamentary systems: list 2 strengths, 2 weaknesses each."},
            {"prompt":"Identify regime changes in 2 countries and explain triggers."}
        ],
        "ideas":["Institutions matter","Democracy has many flavors","Policy ≠ politics"]
    },

    "languages.linguistics": {
        "keywords": ["phonetics","morphology","syntax","semantics","pragmatics","language acquisition"],
        "resources": [
            {"type":"notes","title":"MIT OCW — Linguistics","url":"https://ocw.mit.edu/courses/linguistics-and-philosophy/","why":"Lecture materials from top program."},
            {"type":"notes","title":"Glottopedia","url":"http://www.glottopedia.org/","why":"Community-built linguistic encyclopedia."}
        ],
        "practice": [
            {"prompt":"Break down ‘unbelievable’ into morphemes. Define each part."},
            {"prompt":"Diagram a simple sentence syntactically (tree structure)."}
        ],
        "ideas":["Language is rule-governed","Form ≠ meaning","Context shapes interpretation"]
    },

    "media.studies": {
        "keywords": ["film","television","advertising","representation","genre","audience","narrative"],
        "resources": [
            {"type":"notes","title":"Media Studies 101 (Open Textbook Library)","url":"https://opentextbc.ca/mediastudies101/","why":"Intro open text with theory + examples."},
            {"type":"notes","title":"Film Studies For Free","url":"https://filmstudiesforfree.blogspot.com/","why":"Curated resources & essays."}
        ],
        "practice": [
            {"prompt":"Pick an ad. Analyze representation of gender or class in 200 words."},
            {"prompt":"Identify genre conventions in a film and how they’re subverted."}
        ],
        "ideas":["Media = construction of reality","Audience is active","Representation reflects power"]
    },
        # --- Quant & Data ---

    "stats.intro": {
        "keywords": ["mean","median","mode","variance","standard deviation","normal distribution","hypothesis test","p-value","confidence interval","sampling"],
        "resources": [
            {"type":"notes","title":"OpenStax — Introductory Statistics","url":"https://openstax.org/details/books/introductory-statistics","why":"Free textbook with clear examples."},
            {"type":"notes","title":"Seeing Theory","url":"https://seeing-theory.brown.edu/","why":"Interactive visualizations for core concepts."},
            {"type":"tool","title":"StatKey","url":"http://www.lock5stat.com/StatKey/","why":"Quick simulations and bootstrapping demos."}
        ],
        "practice": [
            {"prompt":"Compute mean/SD and a 95% CI for a sample (n≥30). Interpret in plain language."},
            {"prompt":"Formulate H0/HA and choose a test (z, t, χ²) for a simple scenario; justify choice."}
        ],
        "ideas":["Model → assumptions → test","Effect size > significance","Visualize before you test"]
    },

    "datasci.pandas": {
        "keywords": ["pandas","dataframe","csv","groupby","merge","join","pivot","missing values","plot"],
        "resources": [
            {"type":"notes","title":"Pandas User Guide","url":"https://pandas.pydata.org/docs/user_guide/index.html","why":"Authoritative reference."},
            {"type":"notes","title":"Pandas Cookbook","url":"https://pandas.pydata.org/pandas-docs/stable/user_guide/cookbook.html","why":"Task-oriented recipes."}
        ],
        "practice": [
            {"prompt":"Load a CSV; compute group means and a pivot table; plot a quick bar chart."},
            {"prompt":"Merge two datasets on a key; handle missing values with an explicit policy."}
        ],
        "ideas":["Tidy data wins","Indexing is power","Copy vs view footguns"]
    },

    "ai.ml.basics": {
        "keywords": ["linear regression","logistic regression","overfitting","train test split","cross validation","regularization","features"],
        "resources": [
            {"type":"notes","title":"scikit-learn Tutorials","url":"https://scikit-learn.org/stable/tutorial/index.html","why":"Hands-on ML with code."},
            {"type":"notes","title":"Google ML Crash Course","url":"https://developers.google.com/machine-learning/crash-course","why":"Short lessons with exercises."}
        ],
        "practice": [
            {"prompt":"Fit linear regression on a small dataset; report RMSE and residual plot."},
            {"prompt":"Train/test split, then k-fold CV; compare accuracy with/without regularization."}
        ],
        "ideas":["Bias-variance tradeoff","Data leakage is real","Metrics must match the task"]
    },

    # --- Computing & Web ---

    "prog.python": {
        "keywords": ["python","list comprehension","dict","function","class","exception","virtualenv","typing"],
        "resources": [
            {"type":"notes","title":"Python Tutorial","url":"https://docs.python.org/3/tutorial/","why":"Official, thorough."},
            {"type":"notes","title":"Real Python — Guides","url":"https://realpython.com/","why":"Practical articles and examples."}
        ],
        "practice": [
            {"prompt":"Write a function with type hints; add docstring and tests for 3 edge cases."},
            {"prompt":"Refactor nested loops into comprehensions; handle exceptions cleanly."}
        ],
        "ideas":["Readability first","Pure functions simplify tests","Catch only what you handle"]
    },

    "web.frontend": {
        "keywords": ["html","css","flexbox","grid","responsive","accessibility","aria","react"],
        "resources": [
            {"type":"notes","title":"MDN Web Docs","url":"https://developer.mozilla.org/","why":"The web’s standard reference."},
            {"type":"notes","title":"WebAIM — Accessibility","url":"https://webaim.org/resources/contrastchecker/","why":"Design for all users."}
        ],
        "practice": [
            {"prompt":"Build a responsive 2-column layout with CSS Grid; ensure keyboard navigation works."},
            {"prompt":"Add ARIA labels and test color contrast ratios ≥ 4.5:1."}
        ],
        "ideas":["Mobile-first CSS","Semantic HTML helps everyone","Performance is UX"]
    },

    # --- Natural & Earth Sciences ---

    "env.science": {
        "keywords": ["climate","carbon","biodiversity","ecosystem","lifecycle assessment","sustainability","renewable"],
        "resources": [
            {"type":"data","title":"Our World in Data — Environment","url":"https://ourworldindata.org/environment","why":"Curated datasets and explainers."},
            {"type":"notes","title":"EPA — LCA Basics","url":"https://www.epa.gov/lca","why":"Lifecycle thinking foundations."}
        ],
        "practice": [
            {"prompt":"Draw a system boundary for an LCA of a product; list key impact categories."},
            {"prompt":"Interpret a climate chart: trend, seasonality, and anomalies."}
        ],
        "ideas":["Systems thinking","Measure before you optimize","Tradeoffs are everywhere"]
    },

    "geo.gis": {
        "keywords": ["gis","qgis","coordinate system","projection","shapefile","geopandas","raster","vector"],
        "resources": [
            {"type":"tool","title":"QGIS Documentation","url":"https://docs.qgis.org/","why":"Open-source GIS manual."},
            {"type":"notes","title":"GeoPandas Docs","url":"https://geopandas.org/","why":"Geo with Python DataFrames."}
        ],
        "practice": [
            {"prompt":"Load a shapefile; reproject to Web Mercator; compute area by category."},
            {"prompt":"Join points to polygons (spatial join) and summarize counts."}
        ],
        "ideas":["Projection matters","Spatial joins ≠ table joins","Scale changes meaning"]
    },

    # --- Humanities, Arts, Social ---

    "anthro.culture": {
        "keywords": ["culture","ritual","ethnography","kinship","symbol","fieldwork","participant observation"],
        "resources": [
            {"type":"notes","title":"OpenStax — Anthropology","url":"https://openstax.org/details/books/introduction-anthropology","why":"Free intro text."},
            {"type":"notes","title":"AAA — Teaching Resources","url":"https://www.americananthro.org/","why":"Concept explainers, case examples."}
        ],
        "practice": [
            {"prompt":"Ethnographic sketch: describe a common campus ritual without using insider terms."},
            {"prompt":"Map a kinship diagram and discuss social roles it encodes."}
        ],
        "ideas":["Emic vs etic views","Thick description","Reflexivity in research"]
    },

    "linguistics.phonetics": {
        "keywords": ["ipa","phoneme","allophone","place of articulation","manner","voicing","vowel space"],
        "resources": [
            {"type":"tool","title":"IPA Chart with Audio","url":"https://www.ipachart.com/","why":"Interactive reference."},
            {"type":"notes","title":"UCL Phonetics Resources","url":"https://www.phon.ucl.ac.uk/resource/","why":"Solid primers and exercises."}
        ],
        "practice": [
            {"prompt":"Transcribe 5 words in IPA; mark stress and syllable boundaries."},
            {"prompt":"Classify a set of consonants by place/manner/voicing."}
        ],
        "ideas":["Phoneme ≠ letter","Contrast drives categories","Coarticulation effects are real"]
    },

    "media.rhetoric": {
        "keywords": ["rhetoric","ethos","pathos","logos","argument","persuasion","fallacy"],
        "resources": [
            {"type":"notes","title":"Purdue OWL — Rhetorical Situation","url":"https://owl.purdue.edu/owl/subject_specific_writing/rhetoric_and_logic/index.html","why":"Concise guides with examples."},
            {"type":"notes","title":"Logical Fallacies (UNC)","url":"https://writingcenter.unc.edu/tips-and-tools/fallacies/","why":"Common traps and fixes."}
        ],
        "practice": [
            {"prompt":"Analyze a short op-ed: identify ethos/pathos/logos and one fallacy."},
            {"prompt":"Rewrite a paragraph to strengthen evidence and reduce hedging."}
        ],
        "ideas":["Audience first","Claims need warrants","Clarity beats cleverness"]
    },

    # --- Business, Law, Health ---

    "entrepreneurship.foundations": {
        "keywords": ["mvp","lean","customer discovery","value proposition","pricing","unit economics","churn","lifetime value"],
        "resources": [
            {"type":"notes","title":"Lean Startup Summary (Strategyzer)","url":"https://www.strategyzer.com/blog/posts/the-lean-startup-principles-explained","why":"Core principles distilled."},
            {"type":"tool","title":"Business Model Canvas","url":"https://www.strategyzer.com/canvas/business-model-canvas","why":"One-page model thinking."}
        ],
        "practice": [
            {"prompt":"Draft a value prop: for X who struggle with Y, Teski provides Z, unlike A/B."},
            {"prompt":"Compute LTV from ARPU, gross margin, and churn; sanity-check CAC."}
        ],
        "ideas":["Talk to users","Price the value, not the cost","Focus is a growth cheat code"]
    },

    "law.ip": {
        "keywords": ["copyright","trademark","patent","fair use","license","open source","trade secret"],
        "resources": [
            {"type":"notes","title":"Cornell LII — Intellectual Property","url":"https://www.law.cornell.edu/wex/intellectual_property","why":"Clear definitions & links."},
            {"type":"notes","title":"Choose an Open Source License","url":"https://choosealicense.com/","why":"Practical guide for repos."}
        ],
        "practice": [
            {"prompt":"Classify 5 assets (logo, code, dataset, process, pitch deck) by IP type and protection route."},
            {"prompt":"Assess fair use for a short quote/image in coursework; list risk mitigations."}
        ],
        "ideas":["Registration vs automatic rights","Territoriality matters","Licenses are design choices"]
    },

    "nursing.clinical": {
        "keywords": ["vitals","assessment","care plan","documentation","medication administration","patient safety","SBAR"],
        "resources": [
            {"type":"notes","title":"NurseLabs — Nursing Study Guides","url":"https://nurseslabs.com/","why":"Concise review sheets."},
            {"type":"notes","title":"SBAR Communication Guide","url":"https://www.ihi.org/resources/Pages/Tools/SBARTechniqueforCommunicationASituationalBriefingModel.aspx","why":"Standard handoff model."}
        ],
        "practice": [
            {"prompt":"Create an SBAR for a simulated patient with abnormal vitals."},
            {"prompt":"Draft a care plan: NANDA dx, outcomes, interventions, evaluation."}
        ],
        "ideas":["Safety first","Document like a litigator is reading","Closed-loop communication"]
    },

    # --- Languages (practical) ---

    "language.spanish.a1": {
        "keywords": ["hola","presentarse","saludos","ser","estar","presente","básico","vocabulario"],
        "resources": [
            {"type":"notes","title":"SpanishDict Grammar","url":"https://www.spanishdict.com/guide","why":"Clean grammar explanations."},
            {"type":"practice","title":"Conjuguemos — Verb Practice","url":"https://conjuguemos.com/","why":"Interactive drills."}
        ],
        "practice": [
            {"prompt":"Introduce yourself (5 sentences): name, origin, studies, likes, schedule."},
            {"prompt":"Conjugate ser/estar in present; write 5 contrast sentences using both."}
        ],
        "ideas":["Input before output","High-frequency verbs first","Comprehensible chunks beat lists"]
    },

    "language.french.a1": {
        "keywords": ["bonjour","présentation","présent","être","avoir","vocabulaire","base"],
        "resources": [
            {"type":"notes","title":"ThoughtCo — French Grammar","url":"https://www.thoughtco.com/french-grammar-4133076","why":"Bite-size intros with examples."},
            {"type":"practice","title":"Français Facile — Exercises","url":"https://www.francaisfacile.com/","why":"Lots of graded practice."}
        ],
        "practice": [
            {"prompt":"Présente-toi en 5 phrases; utilise être/avoir et un adjectif."},
            {"prompt":"Écris 5 phrases avec des articles définis/indéfinis; corrige l’accord."}
        ],
        "ideas":["Genres & accords","Prononciation ≠ orthographe","Chunks > rules at first"]
    },

    # --- Study & Presentation Upgrades ---

    "research.sources": {
        "keywords": ["scholarly","peer review","primary source","secondary source","database","citation","plagiarism"],
        "resources": [
            {"type":"notes","title":"JSTOR Open Content","url":"https://about.jstor.org/oa-and-free/","why":"Free articles to cite."},
            {"type":"notes","title":"Google Scholar — Tips","url":"https://scholar.google.com/intl/en/scholar/help.html","why":"Search tactics that save hours."}
        ],
        "practice": [
            {"prompt":"Find 3 peer-reviewed sources for your topic; write 1-sentence relevance for each."},
            {"prompt":"Create a mini annotated bibliography (3–5 items) with citation styles."}
        ],
        "ideas":["Primary vs secondary matters","Abstracts lie—skim methods","Track citations as you go"]
    },

    "presentation.poster": {
        "keywords": ["scientific poster","layout","figure","caption","dpi","typography","conference"],
        "resources": [
            {"type":"notes","title":"Better Posters — Blog","url":"https://betterposters.blogspot.com/","why":"Practical advice that isn’t ugly."},
            {"type":"template","title":"OSF — Poster Templates","url":"https://osf.io/9b6qf/","why":"Starter files you can adapt."}
        ],
        "practice": [
            {"prompt":"Reduce your poster to a title, a single figure, and 3 bullets; rebuild from there."},
            {"prompt":"Write figure captions that tell the result, not just describe the picture."}
        ],
        "ideas":["Eye path left→right","Big takeaway first","One story per poster"]
    },
    "presentation.slides": {
        "keywords": ["slide deck","powerpoint","keynote","google slides","design","typography","visual hierarchy"],
        "resources": [
            {"type":"notes","title":"Garr Reynolds — Presentation Zen","url":"https://www.presentationzen.com/","why":"Design principles for clarity."},
            {"type":"template","title":"SlidesCarnival — Free Templates","url":"https://www.slidescarnival.com/","why":"Professional-looking starter decks."}
        ],
        "practice": [
            {"prompt":"Create a 5-slide deck: title, problem, solution, evidence, call to action."},
            {"prompt":"Redesign a text-heavy slide using images and minimal text."}
        ],
        "ideas":["Less is more","Visuals > text","Consistent style matters"]
    }
}

def resolve_topic(title: str, notes: str | None = None) -> str | None:
    text = f"{title} {notes or ''}".lower()
    for topic, meta in TOPIC_MAP.items():
        for kw in meta["keywords"]:
            if kw in text:
                return topic
    return None