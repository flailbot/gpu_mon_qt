// gddr6_helper.c
// **** Acknowledgement ****
// This code is heavily based on and adapted from the gddr6 project by olealgoritme:
// https://github.com/olealgoritme/gddr6
// Many thanks for their work in identifying the required offsets and method.
// Modifications made for single-run execution and simplified output.
// ************************

#define _GNU_SOURCE

// Include the header if you split definitions, otherwise paste structs/defines here
// #include "gddr6.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <pci/pci.h>
// Removed signal.h as we don't need the cleanup handler for a single run

#define PG_SZ sysconf(_SC_PAGE_SIZE)
#define PRINT_ERROR_STDERR(msg) fprintf(stderr, "Error: %s (at %s:%d)\n", msg, __FILE__, __LINE__)

// --- Device Struct and Table (Copied from original) ---
struct device {
    uint32_t offset;
    uint16_t dev_id;
    char *vram;
    char *arch;
    char *name;
    // Added fields needed during runtime
    pciaddr_t bar0;
    uint16_t bus;
    uint16_t dev;
    uint16_t func;
    off_t phys_addr;
    off_t base_offset;
    void *mapped_addr;
};

struct device dev_table[] = {
    { .offset = 0x0000E2A8, .dev_id = 0x2684, .vram = "GDDR6X", .arch = "AD102", .name =  "RTX 4090" },
    { .offset = 0x0000E2A8, .dev_id = 0x2685, .vram = "GDDR6X", .arch = "AD102", .name =  "RTX 4090 D" },
    { .offset = 0x0000E2A8, .dev_id = 0x2702, .vram = "GDDR6X", .arch = "AD103", .name =  "RTX 4080 Super" },
    { .offset = 0x0000E2A8, .dev_id = 0x2704, .vram = "GDDR6X", .arch = "AD103", .name =  "RTX 4080" },
    { .offset = 0x0000E2A8, .dev_id = 0x2705, .vram = "GDDR6X", .arch = "AD103", .name =  "RTX 4070 Ti Super" },
    { .offset = 0x0000E2A8, .dev_id = 0x2782, .vram = "GDDR6X", .arch = "AD104", .name =  "RTX 4070 Ti" },
    { .offset = 0x0000E2A8, .dev_id = 0x2783, .vram = "GDDR6X", .arch = "AD104", .name =  "RTX 4070 Super" },
    { .offset = 0x0000E2A8, .dev_id = 0x2786, .vram = "GDDR6X", .arch = "AD104", .name =  "RTX 4070" },
    { .offset = 0x0000E2A8, .dev_id = 0x2860, .vram = "GDDR6",  .arch = "AD106", .name =  "RTX 4070 Max-Q / Mobile" },
    { .offset = 0x0000E2A8, .dev_id = 0x2203, .vram = "GDDR6X", .arch = "GA102", .name =  "RTX 3090 Ti" },
    { .offset = 0x0000E2A8, .dev_id = 0x2204, .vram = "GDDR6X", .arch = "GA102", .name =  "RTX 3090" },
    { .offset = 0x0000E2A8, .dev_id = 0x2208, .vram = "GDDR6X", .arch = "GA102", .name =  "RTX 3080 Ti" },
    { .offset = 0x0000E2A8, .dev_id = 0x2206, .vram = "GDDR6X", .arch = "GA102", .name =  "RTX 3080" },
    { .offset = 0x0000E2A8, .dev_id = 0x2216, .vram = "GDDR6X", .arch = "GA102", .name =  "RTX 3080 LHR" },
    { .offset = 0x0000EE50, .dev_id = 0x2484, .vram = "GDDR6",  .arch = "GA104", .name =  "RTX 3070" },
    { .offset = 0x0000EE50, .dev_id = 0x2488, .vram = "GDDR6",  .arch = "GA104", .name =  "RTX 3070 LHR" },
    { .offset = 0x0000E2A8, .dev_id = 0x2531, .vram = "GDDR6",  .arch = "GA106", .name =  "RTX A2000" },
    { .offset = 0x0000E2A8, .dev_id = 0x2571, .vram = "GDDR6",  .arch = "GA106", .name =  "RTX A2000" },
    { .offset = 0x0000E2A8, .dev_id = 0x2232, .vram = "GDDR6",  .arch = "GA102", .name =  "RTX A4500" },
    { .offset = 0x0000E2A8, .dev_id = 0x2231, .vram = "GDDR6",  .arch = "GA102", .name =  "RTX A5000" },
    { .offset = 0x0000E2A8, .dev_id = 0x26B1, .vram = "GDDR6",  .arch = "AD102", .name =  "RTX A6000" },
    { .offset = 0x0000E2A8, .dev_id = 0x27b8, .vram = "GDDR6",  .arch = "AD104", .name =  "L4" },
    { .offset = 0x0000E2A8, .dev_id = 0x26b9, .vram = "GDDR6",  .arch = "AD102", .name =  "L40S" },
    { .offset = 0x0000E2A8, .dev_id = 0x2236, .vram = "GDDR6",  .arch = "GA102", .name =  "A10" },
};
// -------------------------------------------------------

int main(int argc, char *argv[]) {
    int fd = -1;
    struct pci_access *pacc = NULL;
    struct pci_dev *pci_dev = NULL;
    struct device *found_device = NULL; // Pointer to the found device info in dev_table
    ssize_t dev_table_size = (sizeof(dev_table) / sizeof(struct device));
    void *mapped_addr = MAP_FAILED;
    int temp = -1; // Use -1 to indicate error/not found

    // 1. Check privileges early (doesn't guarantee /dev/mem access but is a hint)
    if (geteuid() != 0) {
         PRINT_ERROR_STDERR("Root privileges required to access /dev/mem.");
         return 1; // Exit with error
    }

    // 2. Open /dev/mem
    fd = open("/dev/mem", O_RDONLY | O_SYNC); // Added O_SYNC
    if (fd == -1) {
        PRINT_ERROR_STDERR("Could not open /dev/mem");
        perror("  Reason");
        return 1;
    }

    // 3. Find the first compatible PCI device
    pacc = pci_alloc();
    pci_init(pacc);
    pci_scan_bus(pacc);

    for (pci_dev = pacc->devices; pci_dev != NULL; pci_dev = pci_dev->next) {
        pci_fill_info(pci_dev, PCI_FILL_IDENT | PCI_FILL_BASES | PCI_FILL_CLASS);
        for (uint32_t i = 0; i < dev_table_size; ++i) {
            if (pci_dev->device_id == dev_table[i].dev_id) {
                // Found the first compatible device
                found_device = &dev_table[i]; // Point to the entry in the table
                // Store runtime BAR0 info directly into the found_device struct
                found_device->bar0 = (pci_dev->base_addr[0] & 0xffffffff);
                goto device_found; // Exit loops once found
            }
        }
    }

device_found:
    pci_cleanup(pacc); // Clean up PCI access resources

    if (found_device == NULL) {
        // Optional: Print to stderr if needed, but Python will handle no output
        // PRINT_ERROR_STDERR("No compatible NVIDIA GPU found.");
        close(fd);
        return 1; // Exit, indicating no compatible device found
    }

    // 4. Calculate addresses and Map Memory
    found_device->phys_addr = (found_device->bar0 + found_device->offset);
    found_device->base_offset = found_device->phys_addr & ~(PG_SZ - 1); // Align to page size

    mapped_addr = mmap(0, PG_SZ, PROT_READ, MAP_SHARED, fd, found_device->base_offset);

    if (mapped_addr == MAP_FAILED) {
        PRINT_ERROR_STDERR("Memory mapping failed");
        perror("  Reason");
        fprintf(stderr, "  Check kernel parameters (e.g., iomem=relaxed) and ensure root privileges.\n");
        close(fd);
        return 1;
    }

    // 5. Read Temperature
    // Calculate the virtual address pointing to the exact physical offset
    void *virt_addr = (uint8_t *)mapped_addr + (found_device->phys_addr - found_device->base_offset);
    uint32_t read_result = *((volatile uint32_t *)virt_addr); // Add volatile
    temp = ((read_result & 0x00000fff) / 0x20);

    // 6. Unmap and Close
    munmap(mapped_addr, PG_SZ);
    close(fd);

    // 7. Print ONLY the temperature value to stdout
    printf("%d\n", temp);

    return 0; // Success
}