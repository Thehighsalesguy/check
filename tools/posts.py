"""Post specs. Each photo appears in exactly one post. kind: carousel | reel."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

OUT = os.environ.get('VM_OUT', '/home/claude/work/out')

POSTS = {
 'soda': dict(kind='carousel', adult=False, title=['SODA', 'WALL'], cta1='GRAB YOURS', cta2='SODAS IN STORE NOW', items=[
    dict(src='IMG_2451', mode='cut', name='MOUNTAIN DEW', sub='MANGO PINEAPPLE & CREAM', theme='orange'),
    dict(src='IMG_2453', mode='cut', name='CANADA DRY', sub='LIMITED OFFER CANS', theme='blue'),
    dict(src='IMG_2458', mode='cut', name='ALPINE MIX', sub='ORANGE & COLA', theme='red')]),
 'imports': dict(kind='carousel', adult=False, title=['SNACK', 'RUN'], cta1='SNACK UP', cta2='THE WALL IS STOCKED', items=[
    dict(src='IMG_2381', mode='photo', name='VIDAL GUMMI', sub='SPICY MANGOS', theme='red', fy=.45),
    dict(src='IMG_2459', mode='cut', name='CHEETOS', sub='MASALA BALLS', theme='green', cutkw=dict(min_frac=.3, trim_thin=.4)),
    dict(src='IMG_2450', mode='grid', cuts=['IMG_2450_a','IMG_2450_b','IMG_2450_c','IMG_2450_d'], name='POPCORN WALL', sub='HBAF · 4 FLAVOURS', theme='purple', aw=900, ah=690, ay=880, tilts=[-3, 2, 2, -2])]),
 'rie': dict(kind='carousel', single=True, adult=True, title=['BLUE', 'BEAKER'], items=[
    dict(src='IMG_2433', mode='cut', name='RIE GLASS BEAKER', sub='', theme='blue')]),
 'spoon': dict(kind='carousel', adult=True, title=['SKULL', 'AND BONE'], cta1='COME SEE IT', cta2='SWIRL GLASS IN STORE NOW', items=[
    dict(src='IMG_2402', mode='cut', name='SKULL & BONE', sub='SWIRLED GLASS', theme='purple', pop=1, glow=1, aw=940, ah=700, ay=860),
    dict(src='IMG_2401', mode='cut', name='BONE STEM', sub='SWIRLS FOR DAYS', theme='ink', pop=1, glow=1, aw=940, ah=700, ay=860),
    dict(src='IMG_2400', mode='cut', name='LOOK CLOSER', sub='GLASS ART IN STORE', theme='pink', pop=1, glow=1, aw=940, ah=700, ay=860)]),
 'goblin': dict(kind='carousel', adult=True, title=['MEET THE', 'GOBLIN'], cta1='SAY HI', cta2='GOBLIN BEAKER IN STORE NOW', items=[
    dict(src='IMG_2405', mode='cut', name='GREY BEAKER', sub='GOBLIN ART', theme='purple'),
    dict(src='IMG_2406', mode='cut', name='GOBLIN MODE', sub='FULL DISPLAY', theme='green')]),
 'balls': dict(kind='reel', adult=False, bpm=108, track='funk', hook_theme='ink', hook=[('WHICH BALL', 124, D.WHITE), ('ARE YOU?', 150, D.YEL)],
    item_beats=4, cta='COMMENT YOUR PICK', out1='GRAB A BAG', items=[
    dict(src='IMG_2460', mode='photo', name='MELON BALL', sub='SWEET MELON', theme='green', fy=.55),
    dict(src='IMG_2461', mode='photo', name='CORN BALL', sub='CORN SOUP', theme='yellow', fy=.55),
    dict(src='IMG_2462', mode='photo', name='CHEESE BALL', sub='CHEDDAR CHEESE', theme='orange', fy=.55),
    dict(src='IMG_2463', mode='photo', name='TAKOYAKI BALL', sub='TAKOYAKI FLAVOUR', theme='red', fy=.55)]),
 'gold': dict(kind='reel', adult=True, bpm=140, track='trap', hook_theme='ink', hook=[('GOLD', 170, D.YEL), ('STANDARD', 140, D.WHITE)],
    item_beats=8, out1='COME SEE IT', items=[
    dict(src='IMG_2363', mode='cut', name='GOLD CHROME', sub='MIRROR-FINISH BEAKER', theme='purple'),
    dict(src='IMG_2364', mode='cut', name='SHOW-OFF SHINE', sub='TALL NECK, BIG PRESENCE', theme='pink')]),
 'skull': dict(kind='reel', adult=True, bpm=100, track='synthwave', hook_theme='purple', hook=[('PINK GLASS', 128, D.WHITE), ('BLACK SKULL', 128, D.YEL)],
    item_beats=8, out1='COME SEE IT', items=[
    dict(src='IMG_2403', mode='cut', name='PINK GLASS', sub='RED EYE GLASS', theme='blue'),
    dict(src='IMG_2404', mode='cut', name='SKULL PERC', sub='SPOOKY IN A GOOD WAY', theme='ink')]),
 'sugar': dict(kind='reel', adult=True, bpm=90, track='lofi', hook_theme='ink', hook=[('SUGAR', 160, D.YEL), ('SKULL', 160, D.WHITE)],
    item_beats=8, out1='COME SEE IT', items=[
    dict(src='IMG_2407', mode='cut', name='SUGAR SKULL', sub='FROSTED + BLUE CHROME', theme='yellow'),
    dict(src='IMG_2408', mode='cut', name='FROSTED FINISH', sub='SKULL ART + HYDRO', theme='blue')]),
}

if __name__ == '__main__':
    key = sys.argv[1]; mode = sys.argv[2] if len(sys.argv) > 2 else 'all'
    spec = POSTS[key]; os.makedirs(OUT, exist_ok=True)
    if spec['kind'] == 'carousel':
        n = len(spec['items']) + (0 if spec.get('single') else 1)
        for i in range(n):
            D.carousel_slide(spec, i).save(f'{OUT}/{key}_{i + 1}.jpg', quality=92)
        print('carousel', key, n, 'slides')
    else:
        if mode == 'still':
            D.reel_still(spec, [float(x) for x in sys.argv[3:]] or [1.0, 3.0, 6.0], f'{OUT}/{key}_still.jpg'); print('stills')
        else:
            dur = D.render_reel(spec, f'{OUT}/{key}.mp4', f'/home/claude/work/tmp_{key}'); print('reel', key, round(dur, 1), 's')
