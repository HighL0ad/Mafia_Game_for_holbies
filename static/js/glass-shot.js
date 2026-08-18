/*
 * Procedural shattered-glass scene used when the Mafia's night victim is hit.
 * Cracks are generated for the current viewport so the effect stays sharp on
 * phones and does not repeat the same artificial pattern on every shot.
 */
(function () {
    'use strict';

    let cleanupTimer = null;
    let fractureFrame = null;

    const random = (min, max) => min + Math.random() * (max - min);
    const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

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
        fractureFrame = null;
        overlay.classList.remove('active');
        overlay.hidden = true;
        const canvas = overlay.querySelector('#glass-cracks-canvas');
        const context = canvas && canvas.getContext('2d');
        if (context) context.clearRect(0, 0, canvas.width, canvas.height);
    }

    window.triggerGunshotAndShatter = function triggerGunshotAndShatter() {
        const overlay = document.getElementById('bullet-glass-shatter-overlay');
        const canvas = document.getElementById('glass-cracks-canvas');
        const shards = document.getElementById('glass-shards-container');
        const particles = document.getElementById('glass-particles-container');
        if (!overlay || !canvas || !shards || !particles) return;

        if (cleanupTimer) window.clearTimeout(cleanupTimer);
        if (fractureFrame) cancelAnimationFrame(fractureFrame);

        const width = window.innerWidth;
        const height = window.innerHeight;
        const origin = {
            x: width * random(0.44, 0.56),
            y: height * random(0.40, 0.55)
        };
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const context = prepareCanvas(canvas, width, height);
        const fracture = buildFracture(width, height, origin);

        overlay.style.setProperty('--impact-x', `${origin.x}px`);
        overlay.style.setProperty('--impact-y', `${origin.y}px`);
        overlay.style.setProperty('--tracer-length', `${origin.x + 70}px`);
        createShards(shards, origin, width, height);
        createImpactParticles(particles, origin);

        overlay.hidden = false;
        overlay.classList.remove('active');
        void overlay.offsetWidth;
        overlay.classList.add('active');
        animateFracture(canvas, fracture, reducedMotion);

        cleanupTimer = window.setTimeout(() => clearEffect(overlay), reducedMotion ? 1850 : 3900);
    };
}());
