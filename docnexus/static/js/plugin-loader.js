/**
 * DocNexus Plugin Loader (React Adapter)
 * Enables plugins to register React components into UI slots.
 */

window.DocNexus = window.DocNexus || {};
window.DocNexus._slots = {}; // Map<SlotName, List<Component>>

/**
 * Register a React component for a specific UI slot.
 * @param {string} slotName - The target slot (e.g., 'HEADER_RIGHT').
 * @param {function} component - The React component to render.
 */
window.DocNexus.register = function (slotName, component) {
    if (!window.DocNexus._slots[slotName]) {
        window.DocNexus._slots[slotName] = [];
    }
    window.DocNexus._slots[slotName].push(component);

    // Try to mount immediately if slots are already in DOM
    // In a real app we might want a layout effect or observer, but for now simple polling/init works
    mountPlugins();
};

/**
 * Mounts all registered plugins into their respective DOM slots.
 * Should be called after DOMContentLoaded.
 */
function mountPlugins() {
    if (!window.React || !window.ReactDOM) {
        console.warn("DocNexus: React/ReactDOM not loaded. Skipping plugin mount.");
        return;
    }

    const slots = document.querySelectorAll('[data-plugin-slot]');
    slots.forEach(slotNode => {
        const slotName = slotNode.getAttribute('data-plugin-slot');
        const components = window.DocNexus._slots[slotName] || [];

        // Clear existing content if it was a placeholder (optional logic)
        // For now, we append React roots.

        components.forEach((Component, index) => {
            // Check if already mounted to avoid dupes? 
            // Simplified: Assume separate containers or keyed rendering.

            // Create a unique container for this plugin instance
            const containerId = `plugin-${slotName}-${index}`;
            let container = slotNode.querySelector(`#${containerId}`);

            if (!container) {
                container = document.createElement('div');
                container.id = containerId;
                container.style.display = 'inline-block'; // Default to inline
                slotNode.appendChild(container);

                const root = ReactDOM.createRoot(container);
                root.render(React.createElement(Component));
            }
        });
    });
}

// Auto-mount on load
document.addEventListener('DOMContentLoaded', mountPlugins);
// Also expose mount manually for dynamic updates
window.DocNexus.mount = mountPlugins;
