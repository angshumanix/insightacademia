"""Build intentionally public two-page teaching samples; never full products."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
import json
ROOT=Path(__file__).resolve().parents[1]
FONT=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
if FONT.is_file():
    pdfmetrics.registerFont(TTFont('SampleBody',str(FONT)))
    BODY='SampleBody'
else: BODY='Helvetica'
items=[
 ('case-analysis-workbook','A case, an issue, a reason',[
 ('Teaching example','A student society has fewer repeat visitors at its weekly study sessions. The organisers propose more advertising. In an informal feedback exercise, several visitors say the session time clashes with a regular laboratory class.'),
 ('Identify the issue','Low repeat attendance is the observed problem. It is not yet clear that awareness is the main cause. Separate the observation from the proposed explanation.'),
 ('Connect evidence and action','The timetable feedback suggests a possible access barrier. One practical next step is to ask visitors about alternative times, try a different slot and compare repeat attendance over similar sessions.'),
 ('Reflect','What evidence would make you more confident? Consider how representative the feedback is and what else could explain the attendance pattern.')],['Observed issue','Evidence and its limits','Possible explanation','A reasonable next step']),
 ('literature-review-planner','From individual sources to a theme',[
 ('Teaching example','Imagine two fictional classroom studies about revision habits. Study A reports students using short self-tests. Study B describes students comparing answers with peers. These are invented teaching examples, not research citations.'),
 ('Read separately','For each source, record its question, setting, approach and main finding. Keep your summary distinct from your own interpretation.'),
 ('Connect the ideas','A possible shared theme is how learners check their understanding. A synthesis could compare the role of individual recall with discussion and feedback, while acknowledging the different settings.'),
 ('Reflect','Before treating sources as consistent evidence, ask whether their participants, methods and definitions are comparable. Record a limitation beside each connection.')],['Source and context','Main idea in my words','Connection with another source','Limitation or question']),
 ('revision-study-planner','A purposeful 25-minute study session',[
 ('Teaching example','Choose one topic, such as the difference between revenue and profit. Write a question before opening your notes: Can I explain the difference and give my own example?'),
 ('Try recalling','Spend a few minutes answering from memory. Then check your explanation against your course materials. Note what was missing or confused.'),
 ('Plan a next step','Use the rest of the session to correct the gap and try a fresh example. For instance, a shop can receive sales revenue while its costs leave little profit. Check definitions against your course.'),
 ('Reflect','Choose when to revisit the question. The suggested session length is a planning example, not a claim that one duration works for every learner.')],['Topic and question','My first answer','What I need to revisit','Next review and reflection'])]
for slug,title,notes,fields in items:
    target=ROOT/'assets'/('demo-'+slug+'.pdf')
    c=canvas.Canvas(str(target),pagesize=(595,842),invariant=1)
    c.setTitle('InsightAcademia demonstration: '+title);c.setAuthor('InsightAcademia')
    def text(value,x,y,size=11,color='#18372d',width=475):
        c.setFont(BODY,size);c.setFillColor(HexColor(color))
        lines=simpleSplit(value,BODY,size,width)
        for line in lines:c.drawString(x,y,line);y-=size*1.55
        return y
    def base(page):
        c.setFillColor(HexColor('#F7F5EF'));c.rect(0,0,595,842,fill=1,stroke=0)
        text('INSIGHTACADEMIA',54,790,12)
        c.setStrokeColor(HexColor('#C0A05A'));c.line(54,770,541,770)
        y=text('Demonstration material — not a complete commercial study pack.',54,748,9,width=475)
        c.line(54,65,541,65)
        text('Independent learning sample | Personal study and reference',54,47,8)
        text(str(page)+'/2',518,47,8)
        return y-30
    y=base(1);y=text(title,54,y,20)-20
    for heading,body in notes:
        y=text(heading,54,y,12)-7;y=text(body,54,y,10.5)-19
    c.showPage();y=base(2);y=text('Try it yourself',54,y,22)-12
    y=text('Use your own learning topic. Work through the prompts and return to your course materials to check your understanding.',54,y,10.5)-28
    for field in fields:
        y=text(field,54,y,12)-10
        c.setStrokeColor(HexColor('#c6cfc4'))
        for i in range(3):c.line(54,y,541,y);y-=22
        y-=24
    c.save()
    print(target.name)
