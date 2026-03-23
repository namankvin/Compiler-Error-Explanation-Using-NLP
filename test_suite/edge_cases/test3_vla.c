// Test Case E3: Variable Length Array Issue
// Expected Error: variable length array in struct / invalid use
// Edge Case: VLA restrictions
// Difficulty: Advanced

#include <stdio.h>

struct Buffer {
    int size;
    int data[];  // Flexible array member - special case
};

void create_array(int n) {
    int arr[n];  // VLA - valid but can cause issues
    arr[0] = 10;
    printf("First element: %d\n", arr[0]);
}

int main() {
    create_array(5);
    return 0;
}
