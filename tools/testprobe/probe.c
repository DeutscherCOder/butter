/* Tiny probe binary used to check decompiler output formatting
 * (function prototypes, comma spacing, struct fields). */
#include <stdio.h>

struct point {
    int x;
    int y;
    int z;
};

int add3(int a, int b, int c)
{
    return a + b + c;
}

int scale(struct point *p, int factor)
{
    return (p->x + p->y + p->z) * factor;
}

int main(int argc, char **argv)
{
    struct point p;
    p.x = argc;
    p.y = 2;
    p.z = 3;
    printf("%d %d\n", add3(p.x, p.y, p.z), scale(&p, argc));
    return 0;
}
