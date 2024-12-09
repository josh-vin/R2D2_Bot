// gear_script_template.js

const gearData = {{GEAR_DATA_PLACEHOLDER}};

// Function to update the quantities
function updateQuantities(data) {
    data.forEach(item => {
        let itemName = item.item_name;
        let quantity = item.quantity;
        
        console.log("Updating " + itemName + " to quantity " + quantity);
        // Find the element by the item name
        let itemElement = jQuery("div.item-name").filter(function() {
            return jQuery(this).text().trim() === itemName;
        });
        
        if (itemElement.length) {
            // Find the input element within the same gear container
            let inputElement = itemElement.closest("div.gear-container").find("input[type='number']");
            if (inputElement.length) {
                // Set the value of the input element
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(inputElement[0], quantity);
                
                // Create and dispatch the input event
                let inputEvent = new Event('input', { bubbles: true });
                inputElement[0].dispatchEvent(inputEvent);

                // Create and dispatch the change event
                let changeEvent = new Event('change', { bubbles: true });
                inputElement[0].dispatchEvent(changeEvent);

                // Create and dispatch the blur event
                let blurEvent = new Event('blur', { bubbles: true });
                inputElement[0].dispatchEvent(blurEvent);
            }
        }
    });
}

// Function to reset all quantities to 0
function resetQuantities() {
    jQuery("div.gear-container").each(function() {
        let inputElement = jQuery(this).find("input[type='number']");
        if (inputElement.length) {
            // Set the value of the input element to 0
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeInputValueSetter.call(inputElement[0], 0);

            // Create and dispatch the input event
            let inputEvent = new Event('input', { bubbles: true });
            inputElement[0].dispatchEvent(inputEvent);

            // Create and dispatch the change event
            let changeEvent = new Event('change', { bubbles: true });
            inputElement[0].dispatchEvent(changeEvent);

            // Create and dispatch the blur event
            let blurEvent = new Event('blur', { bubbles: true });
            inputElement[0].dispatchEvent(blurEvent);
            console.log("Set value to 0 for " + inputElement.prevObject[0].innerText.split('\n')[0])
        }
    });
}

// Check if jQuery is loaded
if (typeof jQuery === 'undefined') {
    // If not, load jQuery
    var script = document.createElement('script');
    script.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
    script.onload = function() {
        // Run the resetQuantities function after jQuery is loaded
        resetQuantities();
        // Run the updateQuantities function after reset
        setTimeout(function() {
            updateQuantities(gearData);
        }, 1000); // Delay before updating quantities (adjust delay as needed)
    };
    document.head.appendChild(script);
} else {
    // If jQuery is already loaded, run the functions
    resetQuantities();
    console.log("Quantities reset")
    // Delay before updating quantities (adjust delay as needed)
    setTimeout(function() {
        updateQuantities(gearData);
        console.log("Quantities updated!")
    }, 1000); // Delay before updating quantities (adjust delay as needed)
}
