/*
 * Hybrid WebGL / Canvas shattered-glass scene used when the Mafia's night
 * victim is hit. WebGL refracts a cached image of the live interface while a
 * procedural Canvas renderer remains available as a no-delay fallback.
 */
(function () {
    'use strict';

    let cleanupTimer = null;
    let fractureFrame = null;
    let webglFrame = null;
    let webglRenderer = null;
    let cachedScene = null;
    let cachedScenePromise = null;
    let cachedSceneSize = null;

    const random = (min, max) => min + Math.random() * (max - min);
    const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

    const vertexShaderSource = `
        attribute vec2 a_position;
        varying vec2 v_uv;

        void main() {
            v_uv = a_position * 0.5 + 0.5;
            gl_Position = vec4(a_position, 0.0, 1.0);
        }
    `;

    // The shader is intentionally self-contained: polar cells create the
    // fracture topology, while each cell receives a slightly different UV
    // offset and chromatic split to imitate refraction through uneven glass.
    const fragmentShaderSource = `
        precision highp float;

        uniform sampler2D u_scene;
        uniform vec2 u_resolution;
        uniform vec2 u_impact;
        uniform float u_progress;
        uniform float u_seed;
        varying vec2 v_uv;

        const float PI = 3.141592653589793;
        const float TAU = 6.283185307179586;

        float hash11(float value) {
            return fract(sin(value * 127.1 + u_seed * 311.7) * 43758.5453123);
        }

        float hash21(vec2 value) {
            return fract(sin(dot(value, vec2(127.1, 311.7)) + u_seed * 91.3) * 43758.5453123);
        }

        float valueNoise(vec2 point) {
            vec2 cell = floor(point);
            vec2 local = fract(point);
            local = local * local * (3.0 - 2.0 * local);

            return mix(
                mix(hash21(cell), hash21(cell + vec2(1.0, 0.0)), local.x),
                mix(hash21(cell + vec2(0.0, 1.0)), hash21(cell + vec2(1.0, 1.0)), local.x),
                local.y
            );
        }

        void main() {
            vec2 uv = v_uv;
            float aspect = u_resolution.x / max(u_resolution.y, 1.0);
            vec2 local = uv - u_impact;
            local.x *= aspect;

            float radius = length(local);
            float angle = atan(local.y, local.x);
            float angle01 = (angle + PI) / TAU;
            float rayCount = 14.0 + floor(u_seed * 5.0);
            float angularWarp = (valueNoise(vec2(angle01 * 8.0, radius * 7.0)) - 0.5) * 0.32;

            float spokeCoordinate = angle01 * rayCount
                + sin(radius * 19.0 + u_seed * 8.0) * 0.055
                + angularWarp * min(radius * 1.7, 1.0);
            float spokeCell = floor(spokeCoordinate);
            float spokeFraction = fract(spokeCoordinate);
            float spokeDistance = min(spokeFraction, 1.0 - spokeFraction);
            float spokeWidth = 0.0025 + radius * 0.0025;
            float spoke = 1.0 - smoothstep(spokeWidth, spokeWidth + 0.0065, spokeDistance);
            spoke *= step(0.09, hash11(spokeCell + 3.0));

            float ringCoordinate = radius * (10.4 + hash11(spokeCell) * 2.1)
                + (hash11(spokeCell + 27.0) - 0.5) * 0.72
                + sin(angle * (3.0 + floor(hash11(spokeCell + 8.0) * 3.0)) + u_seed * 9.0) * 0.20
                + (valueNoise(vec2(angle01 * 17.0, radius * 13.0)) - 0.5) * 0.42;
            float ringCell = floor(ringCoordinate);
            float ringFraction = fract(ringCoordinate);
            float ringDistance = min(ringFraction, 1.0 - ringFraction);
            float ring = 1.0 - smoothstep(0.004, 0.014, ringDistance);
            ring *= step(0.43, hash21(vec2(spokeCell, ringCell)));
            ring *= smoothstep(0.025, 0.075, radius);

            float fineCoordinate = angle01 * (rayCount * 2.0 + 3.0)
                + sin(radius * 27.0 + spokeCell) * 0.11;
            float fineFraction = fract(fineCoordinate);
            float fineDistance = min(fineFraction, 1.0 - fineFraction);
            float fine = (1.0 - smoothstep(0.002, 0.007, fineDistance));
            fine *= step(0.58, hash11(floor(fineCoordinate) + 17.0));
            fine *= smoothstep(0.10, 0.22, radius) * 0.58;

            float chipCoordinate = angle01 * 31.0 + sin(radius * 73.0) * 0.10;
            float chipDistance = min(fract(chipCoordinate), 1.0 - fract(chipCoordinate));
            float chip = (1.0 - smoothstep(0.008, 0.022, chipDistance));
            chip *= 1.0 - smoothstep(0.055, 0.14, radius);

            float revealRadius = u_progress * 1.34;
            float reveal = 1.0 - smoothstep(revealRadius, revealRadius + 0.075, radius);
            float crack = max(max(spoke, ring), max(fine, chip)) * reveal;

            vec2 cellId = vec2(spokeCell, ringCell);
            float cellRandom = hash21(cellId);
            vec2 radial = normalize(local + vec2(0.00001));
            vec2 tangent = vec2(-radial.y, radial.x);
            float displacement = (cellRandom - 0.5) * 0.009;
            displacement *= reveal * (1.0 - smoothstep(0.72, 1.24, radius));
            vec2 offset = tangent * displacement;
            offset.x /= aspect;
            offset += radial * ((hash21(cellId + 4.7) - 0.5) * 0.0045 * reveal);

            vec2 sampleUv = clamp(uv + offset, vec2(0.002), vec2(0.998));
            vec3 sceneColor;
            sceneColor.r = texture2D(u_scene, clamp(sampleUv + offset * 0.22, 0.002, 0.998)).r;
            sceneColor.g = texture2D(u_scene, sampleUv).g;
            sceneColor.b = texture2D(u_scene, clamp(sampleUv - offset * 0.18, 0.002, 0.998)).b;

            float facetLight = (cellRandom - 0.5) * 0.10 * reveal;
            sceneColor += vec3(0.67, 0.84, 0.96) * max(facetLight, 0.0);
            sceneColor *= 1.0 + min(facetLight, 0.0);

            float crackCore = smoothstep(0.58, 0.96, crack);
            float crackGlow = smoothstep(0.16, 0.74, crack);
            sceneColor *= 1.0 - crackCore * 0.38;
            sceneColor += vec3(0.76, 0.90, 1.0) * crackGlow * 0.72;

            float impactBloom = (1.0 - smoothstep(0.0, 0.16, radius)) * (1.0 - u_progress);
            sceneColor += vec3(1.0, 0.91, 0.70) * impactBloom * 0.64;
            gl_FragColor = vec4(sceneColor, 1.0);
        }
    `;

    function compileShader(gl, type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.warn('Glass FX shader compilation failed:', gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }
        return shader;
    }

    function createWebGLRenderer(canvas) {
        let gl;
        try {
            gl = canvas.getContext('webgl', {
                alpha: false,
                antialias: false,
                depth: false,
                stencil: false,
                powerPreference: 'high-performance'
            });
        } catch (error) {
            return null;
        }
        if (!gl) return null;

        const vertexShader = compileShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
        const fragmentShader = compileShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);
        if (!vertexShader || !fragmentShader) return null;

        const program = gl.createProgram();
        gl.attachShader(program, vertexShader);
        gl.attachShader(program, fragmentShader);
        gl.linkProgram(program);
        gl.deleteShader(vertexShader);
        gl.deleteShader(fragmentShader);

        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
            console.warn('Glass FX program linking failed:', gl.getProgramInfoLog(program));
            gl.deleteProgram(program);
            return null;
        }

        const positionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.bufferData(
            gl.ARRAY_BUFFER,
            new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
            gl.STATIC_DRAW
        );

        const texture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

        return {
            canvas,
            gl,
            program,
            positionBuffer,
            texture,
            attributes: {
                position: gl.getAttribLocation(program, 'a_position')
            },
            uniforms: {
                scene: gl.getUniformLocation(program, 'u_scene'),
                resolution: gl.getUniformLocation(program, 'u_resolution'),
                impact: gl.getUniformLocation(program, 'u_impact'),
                progress: gl.getUniformLocation(program, 'u_progress'),
                seed: gl.getUniformLocation(program, 'u_seed')
            }
        };
    }

    function renderWebGLFrame(renderer, origin, progress, seed) {
        const { canvas, gl, program, positionBuffer, texture, attributes, uniforms } = renderer;
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.useProgram(program);
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.enableVertexAttribArray(attributes.position);
        gl.vertexAttribPointer(attributes.position, 2, gl.FLOAT, false, 0, 0);
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.uniform1i(uniforms.scene, 0);
        gl.uniform2f(uniforms.resolution, canvas.width, canvas.height);
        gl.uniform2f(
            uniforms.impact,
            origin.x / window.innerWidth,
            1 - origin.y / window.innerHeight
        );
        gl.uniform1f(uniforms.progress, progress);
        gl.uniform1f(uniforms.seed, seed);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }

    function startWebGLGlass(canvas, scene, width, height, origin, reducedMotion) {
        if (!scene) return false;
        if (!webglRenderer || webglRenderer.canvas !== canvas) {
            webglRenderer = createWebGLRenderer(canvas);
        }
        if (!webglRenderer) return false;

        const ratio = Math.min(window.devicePixelRatio || 1, width < 620 ? 1.5 : 2);
        canvas.width = Math.round(width * ratio);
        canvas.height = Math.round(height * ratio);
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        const { gl, texture } = webglRenderer;
        try {
            gl.bindTexture(gl.TEXTURE_2D, texture);
            gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, scene);
        } catch (error) {
            console.warn('Glass FX scene texture could not be uploaded:', error);
            return false;
        }

        const seed = Math.random();
        if (reducedMotion) {
            renderWebGLFrame(webglRenderer, origin, 1, seed);
            return true;
        }

        const startedAt = performance.now();
        const render = now => {
            const elapsed = now - startedAt;
            const linearProgress = clamp(elapsed / 620, 0, 1);
            const easedProgress = 1 - Math.pow(1 - linearProgress, 3);
            renderWebGLFrame(webglRenderer, origin, easedProgress, seed);
            if (elapsed < 900) webglFrame = requestAnimationFrame(render);
        };
        webglFrame = requestAnimationFrame(render);
        return true;
    }

    function sceneMatchesViewport() {
        return cachedScene
            && cachedSceneSize
            && cachedSceneSize.width === window.innerWidth
            && cachedSceneSize.height === window.innerHeight;
    }

    window.prepareGlassShotTexture = function prepareGlassShotTexture(force = false) {
        if (typeof window.html2canvas !== 'function') return Promise.resolve(null);
        if (!force && sceneMatchesViewport()) return Promise.resolve(cachedScene);
        if (cachedScenePromise) return cachedScenePromise;

        const captureWidth = window.innerWidth;
        const captureHeight = window.innerHeight;
        cachedScenePromise = window.html2canvas(document.body, {
            backgroundColor: '#090b10',
            width: captureWidth,
            height: captureHeight,
            windowWidth: captureWidth,
            windowHeight: captureHeight,
            scrollX: window.scrollX,
            scrollY: window.scrollY,
            scale: Math.min(window.devicePixelRatio || 1, 1.5),
            logging: false,
            useCORS: true,
            imageTimeout: 1600,
            ignoreElements: element => [
                'bullet-glass-shatter-overlay',
                'player-phase-overlay',
                'toast-container',
                'glass-refraction-canvas',
                'glass-cracks-canvas'
            ].includes(element.id),
            onclone: clonedDocument => {
                const shotOverlay = clonedDocument.getElementById('bullet-glass-shatter-overlay');
                const phaseOverlay = clonedDocument.getElementById('player-phase-overlay');
                const toastContainer = clonedDocument.getElementById('toast-container');
                if (shotOverlay) shotOverlay.remove();
                if (phaseOverlay) phaseOverlay.remove();
                if (toastContainer) toastContainer.remove();
            }
        }).then(scene => {
            cachedScene = scene;
            cachedSceneSize = { width: captureWidth, height: captureHeight };
            return scene;
        }).catch(error => {
            console.warn('Glass FX pre-capture failed; Canvas fallback will be used:', error);
            return null;
        }).finally(() => {
            cachedScenePromise = null;
        });

        return cachedScenePromise;
    };

    function distanceToViewportEdge(x, y, angle, width, height) {
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        const distances = [];

        if (cos > 0.001) distances.push((width - x) / cos);
        if (cos < -0.001) distances.push(-x / cos);
        if (sin > 0.001) distances.push((height - y) / sin);
        if (sin < -0.001) distances.push(-y / sin);

        return Math.min(...distances.filter(value => value > 0));
    }

    function pointOnRay(ray, targetDistance) {
        if (!ray.length || ray[ray.length - 1].distance < targetDistance) return null;

        for (let i = 1; i < ray.length; i += 1) {
            const previous = ray[i - 1];
            const current = ray[i];
            if (current.distance >= targetDistance) {
                const span = current.distance - previous.distance || 1;
                const amount = (targetDistance - previous.distance) / span;
                return {
                    x: previous.x + (current.x - previous.x) * amount,
                    y: previous.y + (current.y - previous.y) * amount
                };
            }
        }

        return null;
    }

    function addSegment(segments, from, to, distance, kind) {
        const isPrimary = kind === 'primary';
        segments.push({
            from,
            to,
            delay: isPrimary ? 8 + distance * 0.36 : 45 + distance * 0.42,
            duration: isPrimary ? random(38, 72) : random(50, 92),
            width: isPrimary ? random(0.9, 1.55) : random(0.45, 0.92),
            alpha: isPrimary ? random(0.78, 0.98) : random(0.48, 0.76)
        });
    }

    function buildFracture(width, height, origin) {
        const segments = [];
        const rays = [];
        const rayCount = width < 620 ? 13 : 17;
        const angleOffset = random(0, Math.PI * 2);

        for (let rayIndex = 0; rayIndex < rayCount; rayIndex += 1) {
            let angle = angleOffset + (Math.PI * 2 * rayIndex / rayCount) + random(-0.13, 0.13);
            const edgeDistance = distanceToViewportEdge(origin.x, origin.y, angle, width, height) + 24;
            const ray = [{ x: origin.x, y: origin.y, distance: 0 }];
            let point = ray[0];
            let distance = 0;

            while (distance < edgeDistance) {
                const step = Math.min(random(24, 48), edgeDistance - distance);
                angle += random(-0.065, 0.065);
                distance += step;
                const next = {
                    x: point.x + Math.cos(angle) * step,
                    y: point.y + Math.sin(angle) * step,
                    distance
                };

                addSegment(segments, point, next, distance - step, 'primary');
                ray.push(next);
                point = next;
            }

            rays.push(ray);
        }

        // Broken, uneven stress rings make the radial cracks read as real glass.
        const maxRing = Math.min(Math.max(width, height) * 0.52, 430);
        const rings = [30, 55, 88, 132, 188, 258, 350].filter(value => value < maxRing);
        rings.forEach((radius, ringIndex) => {
            for (let rayIndex = 0; rayIndex < rays.length; rayIndex += 1) {
                if (Math.random() < 0.17 + ringIndex * 0.035) continue;

                const start = pointOnRay(rays[rayIndex], radius * random(0.93, 1.06));
                const end = pointOnRay(rays[(rayIndex + 1) % rays.length], radius * random(0.93, 1.06));
                if (!start || !end) continue;

                const middle = {
                    x: (start.x + end.x) / 2 + random(-8, 8),
                    y: (start.y + end.y) / 2 + random(-8, 8)
                };
                addSegment(segments, start, middle, radius, 'web');
                addSegment(segments, middle, end, radius + 5, 'web');
            }
        });

        // Secondary splinters branch away from a subset of the main fractures.
        rays.forEach((ray, rayIndex) => {
            const branchCount = rayIndex % 2 === 0 ? 2 : 1;
            for (let branchIndex = 0; branchIndex < branchCount; branchIndex += 1) {
                if (ray.length < 5) continue;
                const startIndex = Math.floor(random(2, Math.max(3, ray.length - 2)));
                let point = ray[startIndex];
                const radialAngle = Math.atan2(point.y - origin.y, point.x - origin.x);
                let branchAngle = radialAngle + (Math.random() < 0.5 ? -1 : 1) * random(0.38, 0.82);
                let branchDistance = point.distance;

                for (let stepIndex = 0; stepIndex < Math.floor(random(2, 5)); stepIndex += 1) {
                    const step = random(16, 34);
                    branchAngle += random(-0.09, 0.09);
                    const next = {
                        x: point.x + Math.cos(branchAngle) * step,
                        y: point.y + Math.sin(branchAngle) * step
                    };
                    addSegment(segments, point, next, branchDistance + stepIndex * 10, 'branch');
                    point = next;
                }
            }
        });

        // Tiny chipped edges around the entry point keep the bullet hole from
        // looking like a perfect CSS circle.
        for (let chipIndex = 0; chipIndex < 18; chipIndex += 1) {
            const angle = Math.PI * 2 * chipIndex / 18 + random(-0.1, 0.1);
            const innerRadius = random(9, 15);
            const outerRadius = random(19, 42);
            const start = {
                x: origin.x + Math.cos(angle) * innerRadius,
                y: origin.y + Math.sin(angle) * innerRadius
            };
            const end = {
                x: origin.x + Math.cos(angle + random(-0.09, 0.09)) * outerRadius,
                y: origin.y + Math.sin(angle + random(-0.09, 0.09)) * outerRadius
            };
            addSegment(segments, start, end, 0, 'chip');
        }

        return segments;
    }

    function prepareCanvas(canvas, width, height) {
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.round(width * ratio);
        canvas.height = Math.round(height * ratio);
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        const context = canvas.getContext('2d');
        context.setTransform(ratio, 0, 0, ratio, 0, 0);
        return context;
    }

    function drawFracture(context, canvas, segments, elapsed) {
        const width = parseFloat(canvas.style.width);
        const height = parseFloat(canvas.style.height);
        context.clearRect(0, 0, width, height);
        context.lineCap = 'round';
        context.lineJoin = 'round';

        segments.forEach(segment => {
            const rawProgress = clamp((elapsed - segment.delay) / segment.duration, 0, 1);
            if (rawProgress <= 0) return;
            const progress = 1 - Math.pow(1 - rawProgress, 3);
            const endX = segment.from.x + (segment.to.x - segment.from.x) * progress;
            const endY = segment.from.y + (segment.to.y - segment.from.y) * progress;

            // A dark offset and a cold highlight form the two refracting edges.
            context.beginPath();
            context.moveTo(segment.from.x + 1.1, segment.from.y + 1.1);
            context.lineTo(endX + 1.1, endY + 1.1);
            context.strokeStyle = `rgba(0, 8, 15, ${segment.alpha * 0.68})`;
            context.lineWidth = segment.width + 1.4;
            context.stroke();

            context.beginPath();
            context.moveTo(segment.from.x, segment.from.y);
            context.lineTo(endX, endY);
            context.strokeStyle = `rgba(226, 245, 255, ${segment.alpha})`;
            context.shadowColor = 'rgba(172, 224, 255, 0.9)';
            context.shadowBlur = segment.width > 1 ? 4 : 2;
            context.lineWidth = segment.width;
            context.stroke();
            context.shadowBlur = 0;
        });
    }

    function animateFracture(canvas, segments, reducedMotion) {
        const context = canvas.getContext('2d');
        if (!context) return;

        if (reducedMotion) {
            drawFracture(context, canvas, segments, 1000);
            return;
        }

        const startedAt = performance.now();
        const render = now => {
            const elapsed = now - startedAt;
            drawFracture(context, canvas, segments, elapsed);
            if (elapsed < 760) fractureFrame = requestAnimationFrame(render);
        };
        fractureFrame = requestAnimationFrame(render);
    }

    function createShards(container, origin, width, height) {
        const fragment = document.createDocumentFragment();
        const shardCount = width < 620 ? 24 : 34;
        const polygons = [
            '12% 0, 100% 18%, 66% 100%, 0 72%',
            '0 9%, 88% 0, 100% 76%, 35% 100%',
            '48% 0, 100% 100%, 0 74%',
            '0 0, 100% 42%, 58% 100%, 16% 68%'
        ];

        container.replaceChildren();
        for (let index = 0; index < shardCount; index += 1) {
            const shard = document.createElement('i');
            const angle = Math.PI * 2 * index / shardCount + random(-0.2, 0.2);
            const depth = random(0.72, 1.75);
            const travel = random(95, Math.max(width, height) * 0.72) * depth;
            const size = random(8, 27) * depth;
            const delay = random(35, 115);

            shard.className = `glass-shard ${depth > 1.28 ? 'glass-shard-near' : ''}`;
            shard.style.left = `${origin.x + random(-8, 8)}px`;
            shard.style.top = `${origin.y + random(-8, 8)}px`;
            shard.style.width = `${size}px`;
            shard.style.height = `${size * random(0.48, 1.35)}px`;
            shard.style.clipPath = `polygon(${polygons[index % polygons.length]})`;
            shard.style.setProperty('--shard-x', `${Math.cos(angle) * travel}px`);
            shard.style.setProperty('--shard-y', `${Math.sin(angle) * travel + random(35, 150)}px`);
            shard.style.setProperty('--shard-rotate', `${random(-620, 620)}deg`);
            shard.style.setProperty('--shard-scale', depth.toFixed(2));
            shard.style.setProperty('--shard-delay', `${delay}ms`);
            shard.style.setProperty('--shard-duration', `${random(680, 1250)}ms`);
            shard.style.setProperty('--shard-shine', `${random(95, 165)}deg`);
            fragment.appendChild(shard);
        }
        container.appendChild(fragment);
    }

    function createImpactParticles(container, origin) {
        const fragment = document.createDocumentFragment();
        container.replaceChildren();

        for (let index = 0; index < 28; index += 1) {
            const particle = document.createElement('i');
            const angle = random(0, Math.PI * 2);
            const travel = random(45, 190);
            const isSpark = index < 11;

            particle.className = isSpark ? 'glass-spark' : 'glass-dust';
            particle.style.left = `${origin.x}px`;
            particle.style.top = `${origin.y}px`;
            particle.style.setProperty('--particle-x', `${Math.cos(angle) * travel}px`);
            particle.style.setProperty('--particle-y', `${Math.sin(angle) * travel + random(10, 70)}px`);
            particle.style.setProperty('--particle-delay', `${random(12, 95)}ms`);
            particle.style.setProperty('--particle-duration', `${random(380, 850)}ms`);
            particle.style.setProperty('--particle-size', `${random(isSpark ? 1 : 2, isSpark ? 3 : 7)}px`);
            fragment.appendChild(particle);
        }

        container.appendChild(fragment);
    }

    function clearEffect(overlay) {
        if (fractureFrame) cancelAnimationFrame(fractureFrame);
        if (webglFrame) cancelAnimationFrame(webglFrame);
        fractureFrame = null;
        webglFrame = null;
        overlay.classList.remove('active', 'webgl-glass');
        overlay.hidden = true;

        const fallbackCanvas = overlay.querySelector('#glass-cracks-canvas');
        const fallbackContext = fallbackCanvas && fallbackCanvas.getContext('2d');
        if (fallbackContext) {
            fallbackContext.clearRect(0, 0, fallbackCanvas.width, fallbackCanvas.height);
        }

        if (webglRenderer) {
            const { gl } = webglRenderer;
            gl.clearColor(0, 0, 0, 0);
            gl.clear(gl.COLOR_BUFFER_BIT);
        }
    }

    window.triggerGunshotAndShatter = function triggerGunshotAndShatter() {
        const overlay = document.getElementById('bullet-glass-shatter-overlay');
        const refractionCanvas = document.getElementById('glass-refraction-canvas');
        const fallbackCanvas = document.getElementById('glass-cracks-canvas');
        const shards = document.getElementById('glass-shards-container');
        const particles = document.getElementById('glass-particles-container');
        if (!overlay || !refractionCanvas || !fallbackCanvas || !shards || !particles) return;

        if (cleanupTimer) window.clearTimeout(cleanupTimer);
        if (fractureFrame) cancelAnimationFrame(fractureFrame);
        if (webglFrame) cancelAnimationFrame(webglFrame);

        const width = window.innerWidth;
        const height = window.innerHeight;
        const origin = {
            x: width * random(0.44, 0.56),
            y: height * random(0.40, 0.55)
        };
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const scene = sceneMatchesViewport() ? cachedScene : null;
        const webglActive = startWebGLGlass(
            refractionCanvas,
            scene,
            width,
            height,
            origin,
            reducedMotion
        );

        overlay.style.setProperty('--impact-x', `${origin.x}px`);
        overlay.style.setProperty('--impact-y', `${origin.y}px`);
        overlay.style.setProperty('--tracer-length', `${origin.x + 70}px`);
        overlay.classList.toggle('webgl-glass', webglActive);
        createShards(shards, origin, width, height);
        createImpactParticles(particles, origin);

        overlay.hidden = false;
        overlay.classList.remove('active');
        void overlay.offsetWidth;
        overlay.classList.add('active');

        if (!webglActive) {
            prepareCanvas(fallbackCanvas, width, height);
            const fracture = buildFracture(width, height, origin);
            animateFracture(fallbackCanvas, fracture, reducedMotion);
            if (!cachedScenePromise) window.prepareGlassShotTexture();
        } else {
            const fallbackContext = fallbackCanvas.getContext('2d');
            if (fallbackContext) {
                fallbackContext.clearRect(0, 0, fallbackCanvas.width, fallbackCanvas.height);
            }
        }

        cleanupTimer = window.setTimeout(() => clearEffect(overlay), reducedMotion ? 1850 : 3900);
    };

    function scheduleInitialCapture() {
        const capture = () => window.prepareGlassShotTexture();
        if ('requestIdleCallback' in window) {
            window.requestIdleCallback(capture, { timeout: 1600 });
        } else {
            window.setTimeout(capture, 350);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', scheduleInitialCapture, { once: true });
    } else {
        scheduleInitialCapture();
    }

    window.addEventListener('resize', () => {
        cachedScene = null;
        cachedSceneSize = null;
    }, { passive: true });
}());
