"""
Synthetic Multilingual Course Feedback Dataset Generator
========================================================
Generates a realistic, stratified synthetic dataset of 1,000 student course feedback comments
spanning English, Hindi (Devanagari), Marathi (Devanagari), Hinglish, and Marathlish.
Includes controlled temporal drift topics in Terms 3 and 4.
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Set fixed seeds for 100% reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

COURSES = ["DS101", "ML202", "CS303", "AI401", "STAT201", "MATH102"]
INSTRUCTORS = [f"INST_{i:02d}" for i in range(1, 11)]
TERMS = ["Fall 2025", "Spring 2026", "Summer 2026", "Fall 2026"]

# Vocabulary banks per topic and language
TEMPLATES = {
    "TOPIC_1": {  # Pedagogy & Lecture Delivery
        "en": {
            "positive": [
                "The professor explains mathematical derivations with exceptional clarity.",
                "Lectures are well-structured, engaging, and interactive.",
                "Pacing is perfect; complex concepts are broken down into intuitive examples.",
                "Great lecture delivery with relatable real-world machine learning applications."
            ],
            "negative": [
                "The teaching pace is far too fast; slides are rushed through without pausing.",
                "Lectures feel monotonous, dry, and lack interactive engagement.",
                "The professor skips intermediate steps during proofs, making concepts hard to follow.",
                "Slides are cluttered with dense text, and explanations are confusing."
            ],
            "neutral": [
                "Teaching pace is moderate, though more practical examples would help.",
                "The lecture style is standard; slides cover the textbook material directly.",
                "Explanations are adequate, but requires significant self-study after class."
            ]
        },
        "hi": {
            "positive": [
                "प्रोफेसर बहुत ही सहजता और गहराई से हर विषय समझाते हैं।",
                "लेक्चर का तरीका बहुत इंटरैक्टिव और ज्ञानवर्धक है।",
                "पढ़ाने की गति बहुत अच्छी है, कठिन सिद्धांतों को आसान उदाहरणों से समझाया।",
                "कक्षा में सिखाने की शैली बहुत स्पष्ट और प्रेरणादायक है।"
            ],
            "negative": [
                "पढ़ाने की गति बहुत तेज है, विषय ठीक से समझ नहीं आता।",
                "लेक्चर बहुत उबाऊ हो जाते हैं और सिर्फ स्लाइड्स पढ़ दी जाती हैं।",
                "कठिन टॉपिक पर पर्याप्त समय नहीं दिया जाता, सब कुछ जल्दबाजी में खत्म होता है।",
                "व्याख्या स्पष्ट नहीं है, समझने में बहुत कठिनाई होती है।"
            ],
            "neutral": [
                "पढ़ाने का तरीका सामान्य है, लेकिन और अधिक उदाहरणों की आवश्यकता है।",
                "लेक्चर ठीक-ठाक हैं, पर खुद से काफी पढ़ना पड़ता है।"
            ]
        },
        "mr": {
            "positive": [
                "प्राध्यापक प्रत्येक संकल्पना अत्यंत सोप्या भाषेत समजावून सांगतात.",
                "शिकवण्याची पद्धत अतिशय प्रभावी आणि आकर्षक आहे.",
                "वर्गात शिकवण्याचा वेग उत्तम आहे, सर्व उदाहरणे समजतात.",
                "व्याख्याने अत्यंत माहितीपूर्ण आणि प्रेरणादायी असतात."
            ],
            "negative": [
                "शिकवण्याचा वेग खूप जास्त आहे, काहीही नीट समजत नाही.",
                "फक्त स्लाइड्स वाचल्या जातात, सविस्तर स्पष्टीकरण मिळत नाही.",
                "अवघड विषयांवर पुरेशा चर्चा होत नाहीत, फार घाईगडबडीत शिकवले जाते.",
                "शिकवणे कंटाळवाणे वाटते आणि संकल्पना स्पष्ट होत नाहीत."
            ],
            "neutral": [
                "शिकवणे साधारण आहे, अजून सराव उदाहरणे हवी होती.",
                "लेक्चर्स ठीक आहेत, पण स्वतः अभ्यास जास्त करावा लागतो."
            ]
        },
        "hi-en": {
            "positive": [
                "Prof ke explanations bohot clear aur intuitive hain, maza aa gaya.",
                "Teaching style super engaging hai, slide concept easily samajh aate hain.",
                "Pacing bilkul balanced hai, derivations step by step sikhaye jate hain.",
                "Bohot badhiya lecture delivery hai, practical coding examples useful the."
            ],
            "negative": [
                "Pacing bohot fast hai yaar, slides itni jaldi change hoti hain kuch note nahi hota.",
                "Lectures bohot boring aur monotonous ho jate hain, interactive nahi hai.",
                "Prof bina samjhaye direct proofs skip kar dete hain, concepts sar ke upar se nikalte hain.",
                "Teaching style confusing hai, basics clear nahi karwaye."
            ],
            "neutral": [
                "Teaching pace theek-thaak hai, par thode aur practice questions hone chahiye the.",
                "Lecture okayish hain, self study ke bina pass hona mushkil hai."
            ]
        },
        "mr-en": {
            "positive": [
                "Prof che explanations khup clear ahet, concepts mast samjtat.",
                "Teaching style ekdum engaging ahe, interactive sessions changle ahet.",
                "Pacing khup balanced ahe, derivations vyavasthit shikavle jatat."
            ],
            "negative": [
                "Shikavnyacha speed khup fast ahe, kahi note karta yet nahi.",
                "Lectures bore hotat, fakt slides vachun dakhavtat.",
                "Concepts khup confusing vatatat, step-by-step explain karat nahit."
            ],
            "neutral": [
                "Teaching theek ahe, thoda ajun practical examples havet.",
                "Lectures okayish ahet, swatah abhyas karava lagto."
            ]
        }
    },
    "TOPIC_2": {  # Assignments & Homework Load
        "en": {
            "positive": [
                "Assignments were intellectually stimulating and reinforced class concepts.",
                "Homework deadlines were reasonable and allowed sufficient time for research.",
                "Weekly problem sets directly aligned with real-world industry tools."
            ],
            "negative": [
                "Assignment workload is unmanageable alongside other core courses.",
                "Problem set descriptions are extremely ambiguous with conflicting instructions.",
                "Submission deadlines are unrealistic and give no weekend turnaround time."
            ],
            "neutral": [
                "Assignment load is average, but questions could be more clearly phrased.",
                "Workload is manageable if started well in advance of the deadline."
            ]
        },
        "hi": {
            "positive": [
                "असाइनमेंट्स बहुत ज्ञानवर्धक थे और उनसे काफी सीखने को मिला।",
                "गृहकार्य जमा करने की समय सीमा पर्याप्त और उचित थी।",
                "प्रैक्टिकल असाइनमेंट से कोडिंग स्किल्स में काफी सुधार हुआ।"
            ],
            "negative": [
                "असाइनमेंट का बोझ बहुत अधिक है, पूरा करने का समय ही नहीं मिलता।",
                "प्रश्नों के निर्देश बहुत अस्पष्ट और भ्रमित करने वाले हैं।",
                "डेडलाइन बहुत कम दी जाती है, हर हफ्ते बहुत मानसिक तनाव होता है।"
            ],
            "neutral": [
                "असाइनमेंट का स्तर सामान्य है, पर समय पर शुरू करना जरूरी है।"
            ]
        },
        "mr": {
            "positive": [
                "असाइनमेंट्स विचार करायला लावणारे आणि ज्ञानात भर घालणारे होते.",
                "होमवर्क सबमिट करण्यासाठी दिलेली मुदत अगदी योग्य होती.",
                "प्रॅक्टिकल कोडिंग असाइनमेंट्समुळे संकल्पना अधिक स्पष्ट झाल्या."
            ],
            "negative": [
                "असाइनमेंट्सचा ताण प्रचंड आहे, इतर विषयांना वेळच मिळत नाही.",
                "प्रश्नावली अत्यंत क्लिष्ट आणि संदिग्ध सूचनांनी भरलेली आहे.",
                "डेडलाइन खूप कमी वेळात संपते, यामुळे विनाकारण मानसिक ताण येतो."
            ],
            "neutral": [
                "असाइनमेंट्सचे प्रमाण मध्यम आहे, पण प्रश्न अधिक स्पष्ट हवेत."
            ]
        },
        "hi-en": {
            "positive": [
                "Assignments bohot interesting the aur real dataset pe kaam karne ko mila.",
                "Homework submission deadlines reasonable the, stress nahi hua.",
                "Weekly problem sets se theoretical concepts bilkul solid ho gaye."
            ],
            "negative": [
                "Assignment workload bohot zyada heavy hai, deadlines clash karti hain.",
                "Assignment questions ke instructions bohot ambiguous hain, kya expect kar rahe samajh nahi aata.",
                "Har hafte itna lamba assignment dete hain ki doosre subjects ka time nahi bachta."
            ],
            "neutral": [
                "Assignment load theek hai, agar time pe shuru karo toh ho jata hai."
            ]
        },
        "mr-en": {
            "positive": [
                "Assignments khup changle design kele ahet, practical learning zali.",
                "Homework sathi vel purasa dila hota."
            ],
            "negative": [
                "Assignment cha load khup jast ahe, baki subjects la time nahi bhetat.",
                "Problem set instructions ekdum ambiguous ahet, nakki kay karaycha samjat nahi."
            ],
            "neutral": [
                "Assignments normal ahet, thoda time manage karava lagto."
            ]
        }
    },
    "TOPIC_3": {  # Grading Fairness & Rubrics
        "en": {
            "positive": [
                "Grading rubrics were transparent, fair, and distributed before submissions.",
                "TA feedback on exam papers was detailed, constructive, and prompt.",
                "Marking was consistent across all student lab sections."
            ],
            "negative": [
                "Grading feels completely subjective and arbitrary across different TAs.",
                "Zero feedback is provided on docked marks, making it impossible to learn from mistakes.",
                "Exam marking was unusually harsh and punished minor syntactic errors."
            ],
            "neutral": [
                "Grading is strict but adheres to the published rubric guidelines.",
                "Evaluation was moderately prompt, though rubric details were brief."
            ]
        },
        "hi": {
            "positive": [
                "मूल्यांकन बहुत निष्पक्ष और पारदर्शी तरीके से किया गया।",
                "परीक्षा में अंकों के साथ विस्तृत फीडबैक दिया गया जो मददगार था।",
                "मार्किंग स्कीम बिल्कुल स्पष्ट और न्यायसंगत थी।"
            ],
            "negative": [
                "अंक देने में पक्षपात महसूस होता है, कोई स्पष्ट रूब्रिक नहीं है।",
                "मार्क्स क्यों काटे गए इसका कोई कारण या फीडबैक नहीं दिया जाता।",
                "मूल्यांकन बेहद कठोर और अतार्किक था।"
            ],
            "neutral": [
                "मार्किंग थोड़ी सख्त है लेकिन तय नियमों के अनुसार है।"
            ]
        },
        "mr": {
            "positive": [
                "गुणदान अत्यंत पारदर्शक आणि न्याय्य पद्धतीने केले गेले.",
                "तपासणीनंतर मिळालेला अभिप्राय चुका सुधारण्यासाठी खूप उपयुक्त ठरला.",
                "सर्व विद्यार्थ्यांसाठी मूल्यमापन पद्धत समान आणि प्रामाणिक होती."
            ],
            "negative": [
                "मार्क्स देण्यामध्ये प्रचंड पक्षपातीपणा दिसून येतो.",
                "गुण का कापले याचे कोणतेही स्पष्टीकरण दिले जात नाही.",
                "परीक्षेचे चेकिंग खूप अवाजवी कडक करण्यात आले."
            ],
            "neutral": [
                "चेकिंग कडक आहे पण दिलेल्या नियमांनुसारच आहे."
            ]
        },
        "hi-en": {
            "positive": [
                "Grading rubric ekdum fair aur transparent tha, koi bias nahi dikha.",
                "TA ne paper check karke detailed feedback diya ki kahan marks kate.",
                "Marking criteria bilkul clear tha."
            ],
            "negative": [
                "Grading bohot arbitrary aur unfair lagti hai, TAs ke mood pe depend karta hai.",
                "Marks deduct kar diye par koi comments ya feedback nahi diya.",
                "Paper checking bohot strict aur unforgiving thi, minor typo pe bhi zero de diya."
            ],
            "neutral": [
                "Grading strict hai but standard rubric follow kiya gaya."
            ]
        },
        "mr-en": {
            "positive": [
                "Grading ekdum fair hoti, sarvanna consistent marks dile.",
                "Paper checking nanter changla feedback dila."
            ],
            "negative": [
                "Marking madhe khup partiality vatate, rubrics clear nahit.",
                "Marks kashala cut kele he sangitlech nahi."
            ],
            "neutral": [
                "Evaluation thoda strict ahe pan acceptable ahe."
            ]
        }
    },
    "TOPIC_4": {  # Faculty Support & Availability
        "en": {
            "positive": [
                "The professor is exceptionally welcoming and patient during office hours.",
                "Forum queries on discussion boards were answered within a couple of hours.",
                "Faculty went out of their way to offer extra mentoring and academic guidance."
            ],
            "negative": [
                "The instructor is dismissive during doubt sessions and rarely answers emails.",
                "Office hours are frequently canceled without prior notification.",
                "Reaching the professor outside class is nearly impossible; discussion forums are ignored."
            ],
            "neutral": [
                "Faculty is accessible primarily through scheduled office hours, not email.",
                "Support is available if students actively approach during designated hours."
            ]
        },
        "hi": {
            "positive": [
                "प्रोफेसर संशय दूर करने के लिए हमेशा तत्पर और विनम्र रहते हैं।",
                "ऑफिस आवर्स में उनका मार्गदर्शन बहुत मूल्यवान और प्रेरक रहा।",
                "ईमेल और फोरम पर पूछे गए सवालों का उत्तर बहुत जल्दी मिलता है।"
            ],
            "negative": [
                "प्रोफेसर सवाल पूछने पर झिड़क देते हैं और ईमेल का कोई जवाब नहीं देते।",
                "ऑफिस आवर्स बिना किसी सूचना के रद्द कर दिए जाते हैं।",
                "कक्षा के बाहर प्रोफेसर से संपर्क करना लगभग असंभव है।"
            ],
            "neutral": [
                "प्रोफेसर सिर्फ तय समय पर ही उपलब्ध होते हैं।"
            ]
        },
        "mr": {
            "positive": [
                "शंका निरसन सत्रात शिक्षक अत्यंत आदरपूर्वक आणि शांतपणे मदत करतात.",
                "फोरमवर विचारलेल्या प्रश्नांना तातडीने उत्तरे दिली जातात.",
                "विद्यार्थ्यांना अतिरिक्त मार्गदर्शन करण्यासाठी प्राध्यापक सदैव तत्पर असतात."
            ],
            "negative": [
                "शिक्षकांशी संपर्क साधणे अत्यंत कठीण आहे, ईमेलला प्रतिसाद मिळत नाही.",
                "ऑफिस अवर्स अचानक रद्द केले जातात.",
                "डाऊट्स विचारल्यास दुर्लक्ष केले जाते, योग्य सहकार्य मिळत नाही."
            ],
            "neutral": [
                "प्राध्यापक केवळ ठरवून दिलेल्या वेळेतच भेटतात."
            ]
        },
        "hi-en": {
            "positive": [
                "Prof office hours me bohot supportive hain, doubts easily clear karte hain.",
                "Discussion board pe fast replies milte hain, faculty genuinely cares.",
                "Guidance bohot achha mila project ke liye."
            ],
            "negative": [
                "Prof bohot unapproachable lagte hain, doubts pucho toh daant dete hain.",
                "Emails ka koi reply nahi aata, office hours cancel kar diye jate hain.",
                "Class ke baad consult karna impossible hai, forum bilkul dead hai."
            ],
            "neutral": [
                "Faculty sirf official timing me available rehte hain."
            ]
        },
        "mr-en": {
            "positive": [
                "Prof khup helpful ahet, office hours madhe changli madat keli.",
                "Doubts solve karayla nehmi ready astat."
            ],
            "negative": [
                "Prof doubts vicharlyavar irritate hotat, emails na reply det nahit.",
                "Office hours often cancel hotat, contact hot nahi."
            ],
            "neutral": [
                "Faculty only scheduled veles available astat."
            ]
        }
    },
    "TOPIC_5": {  # Lab & Technical Infrastructure
        "en": {
            "positive": [
                "The computer lab hardware and cloud GPU instances performed flawlessly.",
                "Software tools and Python libraries were pre-configured without dependency issues.",
                "High-speed campus Wi-Fi and updated terminals made lab practicals seamless."
            ],
            "negative": [
                "Lab workstations crashed continuously during machine learning model training.",
                "Campus Wi-Fi drops constantly during timed lab practical exams.",
                "Outdated software versions caused persistent environment and package errors."
            ],
            "neutral": [
                "Lab facilities are adequate for basic tasks, though GPUs are limited.",
                "Hardware works fine, but software environment requires manual setup."
            ]
        },
        "hi": {
            "positive": [
                "कंप्यूटर लैब और सर्वर की सुविधा बहुत आधुनिक और तेज है।",
                "सॉफ्टवेयर और टूल्स पहले से इंस्टॉल थे जिससे प्रैक्टिकल में कोई रुकावट नहीं आई।",
                "हाई-स्पीड इंटरनेट और अच्छे सिस्टम से काम करना बहुत आसान रहा।"
            ],
            "negative": [
                "लैब के कंप्यूटर बार-बार क्रैश होते हैं, जिससे कोड नष्ट हो जाता है।",
                "प्रैक्टिकल के दौरान वाई-फाई कनेक्शन बार-बार कट जाता है।",
                "सिस्टम में सॉफ्टवेयर बहुत पुराने हैं और लाइब्रेरी काम नहीं करतीं।"
            ],
            "neutral": [
                "लैब की सुविधाएं बुनियादी कोडिंग के लिए ठीक हैं।"
            ]
        },
        "mr": {
            "positive": [
                "संगणक प्रयोगशाळेतील उपकरणे आणि जीपीयूपी (GPU) सुविधा अतिशय आधुनिक आहेत.",
                "सॉफ्टवेअर सेटअप सुरळीत असल्यामुळे प्रॅक्टिकल्स वेळेत पूर्ण झाले.",
                "लॅबमधील इंटरनेट आणि संगणक अत्यंत वेगवान आणि अद्ययावत आहेत."
            ],
            "negative": [
                "प्रॅक्टिकल करताना संगणक वारंवार हँग होतात आणि बंद पडतात.",
                "लॅबमधील वाय-फाय सतत डिस्कनेक्ट होते, कोडिंग थांबवावे लागते.",
                "सॉफ्टवेअरचे जुने व्हर्जन्स असल्यामुळे एरर्स सारख्या येतात."
            ],
            "neutral": [
                "लॅब बेसिक कामासाठी पुरेशी आहे, पण रिसोर्सेस मर्यादित आहेत."
            ]
        },
        "hi-en": {
            "positive": [
                "Lab machines ekdum smooth chalti hain, GPU server ka setup best tha.",
                "Python packages pre-installed the, environment setup me time waste nahi hua.",
                "High speed internet and updated PCs se practicals smoothly ho gaye."
            ],
            "negative": [
                "Lab systems lagatar crash hote hain, model train karte hi shutdown ho gaya.",
                "Lab me wifi signal bohot weak hai, practical test me submit nahi ho paya.",
                "Outdated software versions hain lab PCs me, packages install nahi hote."
            ],
            "neutral": [
                "Lab hardware basic assignments ke liye theek hai."
            ]
        },
        "mr-en": {
            "positive": [
                "Lab computers fast ahet, GPU servers changle operate zale.",
                "Lab setup madhe kahi issue ala nahi."
            ],
            "negative": [
                "Lab computers सारखे crash hotat, code save hot nahi.",
                "Wifi disconnection mule khup tras hoto lab exam madhe.",
                "Old software installed ahe lab PCs var."
            ],
            "neutral": [
                "Lab setup okay ahe, basic python chalto."
            ]
        }
    },
    "TOPIC_6": {  # Curriculum Depth & Relevance
        "en": {
            "positive": [
                "The syllabus is modern, comprehensive, and aligns with modern data industry standards.",
                "Theoretical foundations of algorithms were matched with hands-on code.",
                "Case studies covered state-of-the-art architectures and transformer models."
            ],
            "negative": [
                "The syllabus is outdated and teaches deprecated libraries from a decade ago.",
                "Too much focus on rote memorization of formulas rather than applied data problem-solving.",
                "Prerequisites were not honored; the course assumed advanced knowledge not taught earlier."
            ],
            "neutral": [
                "The curriculum covers basic foundations, though newer AI topics were omitted.",
                "Syllabus scope is standard for an undergraduate course."
            ]
        },
        "hi": {
            "positive": [
                "पाठ्यक्रम बहुत आधुनिक और उद्योग की वर्तमान आवश्यकताओं के अनुकूल है।",
                "थ्योरी और प्रैक्टिकल का संतुलन बहुत सराहनीय है।",
                "नए एल्गोरिदम और केस स्टडीज को पाठ्यक्रम में शामिल किया गया है।"
            ],
            "negative": [
                "सिलेबस बहुत पुराना है और अब इस्तेमाल न होने वाली तकनीकें सिखाई जा रही हैं।",
                "केवल रटने पर जोर दिया जाता है, वास्तविक समस्या समाधान पर नहीं।",
                "मूल विषयों को सिखाए बिना सीधे कठिन एडवांस गणित शुरू कर दिया गया।"
            ],
            "neutral": [
                "पाठ्यक्रम बुनियादी स्तर के लिए पर्याप्त है।"
            ]
        },
        "mr": {
            "positive": [
                "अभ्यासक्रम अत्यंत आधुनिक आणि उद्योग जगतातील कौशल्यांना पूरक आहे.",
                "सिद्धांत आणि प्रात्यक्षिक यांचा समतोल अतिशय उत्तम राखला आहे.",
                "नवीन तंत्रज्ञानाचा समावेश असल्यामुळे खूप काही शिकायला मिळाले."
            ],
            "negative": [
                "अभ्यासक्रम जुनाट असून कालबाह्य पद्धती शिकवल्या जात आहेत.",
                "फक्त सूत्रे पाठ करण्यावर भर आहे, प्रत्यक्ष उपयोजन शिकवले जात नाही.",
                "पायाभूत संकल्पना स्पष्ट न करता थेट प्रगत विषय शिकवले गेले."
            ],
            "neutral": [
                "अभ्यासक्रम सर्वसाधारण पदवी स्तरासाठी ठीक आहे."
            ]
        },
        "hi-en": {
            "positive": [
                "Syllabus ekdum updated aur industry relevant hai, modern ML tools cover kiye.",
                "Theory aur real-world code implementation ka solid balance tha.",
                "Curriculum bohot comprehensive aur informative laga."
            ],
            "negative": [
                "Curriculum bohot outdated hai, puraane algorithms padha rahe hain jo koi use nahi karta.",
                "Course me practical application kam aur formula ratta-marne pe zyada dhyan hai.",
                "Prerequisites properly set nahi the, assumed knowledge ki wajah se struggle hua."
            ],
            "neutral": [
                "Syllabus average hai, basics cover ho jate hain."
            ]
        },
        "mr-en": {
            "positive": [
                "Curriculum khup relevant ahe, latest industry standards cover kele.",
                "Theory ani practical balance chhan hota."
            ],
            "negative": [
                "Syllabus khup outdated ahe, junya libraries shikavtat.",
                "Practical coding kam ahe, fakt theory var bhar ahe."
            ],
            "neutral": [
                "Curriculum standard ahe degree course sathi."
            ]
        }
    },
    "DRIFT_1": {  # Emergent Drift: GenAI & Academic Integrity Policy (Terms 3 and 4)
        "en": {
            "positive": [
                "The transparent guidelines on using ChatGPT and Copilot for coding assistance were helpful.",
                "Clear policy allowing AI brainstorming while requiring attribution in homework.",
                "Constructive discussion on ethical Generative AI use in coursework."
            ],
            "negative": [
                "The university AI detector gave false positive plagiarism flags on original student code.",
                "Complete lack of clear policy on whether using ChatGPT for debugging assignments is permitted.",
                "Arbitrary penalties applied because automated AI checkers flagged standard boilerplate code."
            ],
            "neutral": [
                "The department should clarify the official policy on generative AI tools in coding assignments.",
                "AI tool policy was briefed briefly, but students are still uncertain about rules."
            ]
        },
        "hi": {
            "positive": [
                "असाइनमेंट में चैटजीपीटी (ChatGPT) के सही उपयोग पर स्पष्ट दिशा-निर्देश बहुत उपयोगी रहे।",
                "एआई टूल्स के नैतिक उपयोग पर दी गई छूट और मार्गदर्शन सराहनीय है।"
            ],
            "negative": [
                "एआई डिटेक्टर ने खुद से लिखे गए कोड को भी गलत तरीके से साहित्यिक चोरी (plagiarism) बता दिया।",
                "चैटजीपीटी के इस्तेमाल पर कोई स्पष्ट नियम नहीं है, बिना वजह पेनल्टी का डर बना रहता है।",
                "एआई डिटेक्टर टूल्स पूरी तरह अविश्वसनीय हैं और निर्दोष छात्रों के अंक काट रहे हैं।"
            ],
            "neutral": [
                "कॉलेज को कोडिंग असाइनमेंट्स में जनरेटिव एआई के उपयोग पर स्पष्ट नीति जारी करनी चाहिए।"
            ]
        },
        "mr": {
            "positive": [
                "कोडिंगमध्ये एआय टूल्स (ChatGPT) च्या वापराबाबतचे नियम स्पष्ट आणि मार्गदर्शक होते.",
                "कृत्रिम बुद्धिमत्ता टूल्सचा अभ्यासात योग्य वापर कसा करावा हे स्पष्ट केले."
            ],
            "negative": [
                "एआय डिटेक्टरने स्वतः लिहिलेल्या मूळ कोडवरही बनावट प्लेगिअरिझमचा आरोप लावला.",
                "चॅटजीपीटी वापरण्याबाबत कोणतेही स्पष्ट धोरण नसल्यामुळे गोंधळ निर्माण झाला आहे.",
                "एआय डिटेक्शन सॉफ्टवेअर चुकीच्या पद्धतीने मार्क्स कापत आहे."
            ],
            "neutral": [
                "विद्यापीठाने एआय साधनांच्या वापरावर अधिकृत मार्गदर्शक तत्त्वे जाहीर करावीत."
            ]
        },
        "hi-en": {
            "positive": [
                "ChatGPT aur GitHub Copilot usage pe policy bohot sensible aur clear thi.",
                "Prof ne explain kiya ki debugging ke liye AI tools kaise ethically use karein."
            ],
            "negative": [
                "AI detector ne mere original code ko false positive plagiarism flag kar diya, totally unfair.",
                "ChatGPT use karne pe kya rules hain kuch clearly bataya hi nahi, marks kat gaye.",
                "AI copy checker tool ekdum broken hai, boiler-plate python code pe cheating bolta hai."
            ],
            "neutral": [
                "GenAI policy par thoda aur clarity chahiye assignment submissions ke time."
            ]
        },
        "mr-en": {
            "positive": [
                "AI tools vaparanyache rules changle explain kele.",
                "ChatGPT ethically kasa vapraycha he guidelines clear hotya."
            ],
            "negative": [
                "AI detector tool mule original assignment var false cheating allegation ala.",
                "ChatGPT rules clear nahit, kiti use karu shakto kahi sangitla nahi."
            ],
            "neutral": [
                "AI policy clear asavi pratyek assignment sathi."
            ]
        }
    },
    "DRIFT_2": {  # Emergent Drift: Hybrid Lecture Audio/Video & Logistics (Term 4)
        "en": {
            "positive": [
                "Hybrid classroom microphone setup and 4K camera tracking made remote lectures seamless.",
                "Audio quality on the live stream was crisp and classroom questions were easily audible.",
                "Instant upload of high-definition hybrid lecture recordings saved commuter students."
            ],
            "negative": [
                "The lapel microphone kept cutting out during hybrid lectures, making online audio unintelligible.",
                "Camera remained fixed on the whiteboard without focusing on professor derivations during streams.",
                "Severe echo and audio lag during hybrid sessions made attending remotely frustrating."
            ],
            "neutral": [
                "Hybrid setup works reasonably well, though the classroom mic occasionally picks up room noise.",
                "Remote stream video is clear, but audio volume needs slight calibration."
            ]
        },
        "hi": {
            "positive": [
                "हाइब्रिड क्लासरूम का ऑडियो और वीडियो सेटअप बहुत शानदार और स्पष्ट था।",
                "रिमोट लेक्चर की रिकॉर्डिंग बहुत तेजी से पोर्टल पर उपलब्ध कराई गई।"
            ],
            "negative": [
                "हाइब्रिड क्लास के दौरान माइक बार-बार बंद हो जाता है, कुछ सुनाई नहीं देता।",
                "कैमरा बोर्ड पर फोकस नहीं करता और लाइव स्ट्रीम में आवाज बहुत गूंजती (echo) है।",
                "ऑनलाइन जुड़ने वाले छात्रों को ऑडियो लैग के कारण बहुत परेशानी हुई।"
            ],
            "neutral": [
                "हाइब्रिड क्लास की तकनीकी व्यवस्था सामान्य है, पर माइक सुधारा जा सकता है।"
            ]
        },
        "mr": {
            "positive": [
                "हायब्रिड लेक्चरचे ऑडिओ आणि व्हिडिओ प्रसारण अत्यंत स्पष्ट आणि दर्जेदार होते.",
                "ऑनलाइन लेक्चर्सचे रेकॉर्डिंग वेळेवर मिळाल्यामुळे रिव्हिजन करणे सोपे झाले."
            ],
            "negative": [
                "हायब्रिड क्लासमध्ये माईक सतत कट होतो, शिक्षकांचा आवाज अजिबात ऐकू येत नाही.",
                "कॅमेऱ्याचा फोकस फळ्यावर नसतो आणि प्रचंड इको (echo) येतो.",
                "ऑनलाइन उपस्थित असणाऱ्या विद्यार्थ्यांसाठी ध्वनी दर्जा अत्यंत निकृष्ट होता."
            ],
            "neutral": [
                "हायब्रिड सेटअप सर्वसाधारण आहे, पण आवाजाची स्पष्टता वाढवणे गरजेचे आहे."
            ]
        },
        "hi-en": {
            "positive": [
                "Hybrid lectures ka camera tracking and mic audio ekdum crystal clear tha.",
                "Classroom recording time pe upload ho gayi online portal pe."
            ],
            "negative": [
                "Hybrid lecture me mic aawaj bar-bar cut ho rahi thi, online sunna impossible ho gaya.",
                "Camera board pe blur dikhata hai aur severe echo problem hai hybrid session me.",
                "Mic issue ki wajah se online students ke half concepts miss ho gaye."
            ],
            "neutral": [
                "Hybrid stream theek hai par audio level balance karna padega."
            ]
        },
        "mr-en": {
            "positive": [
                "Hybrid lecture cha mic ani camera quality changla hota.",
                "Recorded sessions time var LMS var upload zale."
            ],
            "negative": [
                "Hybrid class madhe mic aawaj break hoto, kahi aiku yet nahi online.",
                "Camera focus hot nahi ani video lag khup hoto hybrid stream madhe."
            ],
            "neutral": [
                "Hybrid system average ahe, audio improve zala pahije."
            ]
        }
    }
}

# Conjunctions for compound comments
CONJUNCTIONS = {
    "en": [" However, ", " On the other hand, ", " But ", " Nonetheless, "],
    "hi": [" लेकिन, ", " परन्तु, ", " दूसरी तरफ, "],
    "mr": [" परंतु, ", " मात्र, ", " दुसऱ्या बाजूला, "],
    "hi-en": [" But ", " Par doosri taraf, ", " However, ", " Lekin "],
    "mr-en": [" Pan ", " But dusrya bajula, ", " However, "]
}

def generate_sample(target_term: str, sample_idx: int) -> dict:
    """Generates a single synthetic feedback comment with metadata and labels."""
    # Determine language distribution
    # en: 35%, hi: 20%, mr: 15%, hi-en: 20%, mr-en: 10%
    lang = random.choices(
        ["en", "hi", "mr", "hi-en", "mr-en"],
        weights=[0.35, 0.20, 0.15, 0.20, 0.10],
        k=1
    )[0]

    script_map = {
        "en": "Latin",
        "hi": "Devanagari",
        "mr": "Devanagari",
        "hi-en": "Latin",
        "mr-en": "Latin"
    }
    script = script_map[lang]

    # Available topics based on academic term (simulating temporal drift)
    available_topics = ["TOPIC_1", "TOPIC_2", "TOPIC_3", "TOPIC_4", "TOPIC_5", "TOPIC_6"]
    
    # In Term 3 (Summer 2026), DRIFT_1 emerges
    if target_term == "Summer 2026":
        # 15% probability of DRIFT_1
        if random.random() < 0.16:
            primary_topic = "DRIFT_1"
        else:
            primary_topic = random.choice(available_topics)
    # In Term 4 (Fall 2026), both DRIFT_1 and DRIFT_2 are active
    elif target_term == "Fall 2026":
        p = random.random()
        if p < 0.14:
            primary_topic = "DRIFT_1"
        elif p < 0.28:
            primary_topic = "DRIFT_2"
        else:
            primary_topic = random.choice(available_topics)
    else:
        primary_topic = random.choice(available_topics)

    is_drift = primary_topic in ["DRIFT_1", "DRIFT_2"]

    # Sentiment distribution: 40% pos, 40% neg, 20% neu
    sentiment_primary = random.choices(
        ["positive", "negative", "neutral"],
        weights=[0.40, 0.40, 0.20],
        k=1
    )[0]

    # Select text for primary topic
    primary_text = random.choice(TEMPLATES[primary_topic][lang][sentiment_primary])

    # 30% chance of compound multi-aspect comment (if not drift topic, to keep drift clean)
    secondary_topic = None
    aspect_dict = {primary_topic: sentiment_primary}

    if not is_drift and random.random() < 0.30:
        other_topics = [t for t in available_topics if t != primary_topic]
        secondary_topic = random.choice(other_topics)
        # Contrastive sentiment for realism (if primary positive -> secondary negative)
        if sentiment_primary == "positive":
            sentiment_secondary = "negative"
        elif sentiment_primary == "negative":
            sentiment_secondary = "positive"
        else:
            sentiment_secondary = random.choice(["positive", "negative"])

        secondary_text = random.choice(TEMPLATES[secondary_topic][lang][sentiment_secondary])
        conj = random.choice(CONJUNCTIONS[lang])
        full_text = f"{primary_text}{conj}{secondary_text}"
        aspect_dict[secondary_topic] = sentiment_secondary
        overall_sentiment = "neutral"  # mixed compound
    else:
        full_text = primary_text
        overall_sentiment = sentiment_primary

    # Generate timestamp within the semester
    term_dates = {
        "Fall 2025": (datetime(2025, 9, 1), datetime(2025, 12, 20)),
        "Spring 2026": (datetime(2026, 1, 10), datetime(2026, 5, 15)),
        "Summer 2026": (datetime(2026, 6, 1), datetime(2026, 7, 31)),
        "Fall 2026": (datetime(2026, 9, 1), datetime(2026, 12, 20))
    }
    start_dt, end_dt = term_dates[target_term]
    delta_days = (end_dt - start_dt).days
    random_days = random.randint(0, delta_days)
    random_seconds = random.randint(0, 86400)
    ts = start_dt + timedelta(days=random_days, seconds=random_seconds)

    return {
        "comment_id": str(uuid.uuid4()),
        "timestamp": ts.isoformat(),
        "academic_term": target_term,
        "course_code": random.choice(COURSES),
        "instructor_id": random.choice(INSTRUCTORS),
        "raw_text": full_text,
        "true_language": lang,
        "script_type": script,
        "primary_topic": primary_topic,
        "secondary_topic": secondary_topic,
        "aspect_sentiment": json.dumps(aspect_dict, ensure_ascii=False),
        "overall_sentiment": overall_sentiment,
        "is_emergent_drift": is_drift
    }

def main():
    print("=" * 70)
    print("Generating 600 Multilingual Course Feedback Comments...")
    print("=" * 70)

    records = []
    # 150 comments per term across 4 terms = 600 comments total
    for term in TERMS:
        for i in range(150):
            sample = generate_sample(term, i)
            records.append(sample)

    df = pd.DataFrame(records)

    # Sort chronologically by timestamp
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp_dt").reset_index(drop=True)
    df = df.drop(columns=["timestamp_dt"])

    # Ensure output directories exist
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    raw_path = os.path.join("data", "raw", "synthetic_feedback_600.csv")
    df.to_csv(raw_path, index=False, encoding="utf-8")
    print(f"[+] Saved raw dataset to {raw_path} ({len(df)} records)")

    # Stratified Train / Val / Test Split (70% Train, 15% Val, 15% Test)
    # Stratify by true_language to ensure exact multilingual distribution
    train_df, test_val_df = train_test_split(
        df,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=df["true_language"]
    )

    val_df, test_df = train_test_split(
        test_val_df,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=test_val_df["true_language"]
    )

    # Verify zero leakage (no common comment_ids)
    train_ids = set(train_df["comment_id"])
    val_ids = set(val_df["comment_id"])
    test_ids = set(test_df["comment_id"])

    assert len(train_ids.intersection(val_ids)) == 0, "Data leakage detected between train and val!"
    assert len(train_ids.intersection(test_ids)) == 0, "Data leakage detected between train and test!"
    assert len(val_ids.intersection(test_ids)) == 0, "Data leakage detected between val and test!"

    train_path = os.path.join("data", "processed", "train.csv")
    val_path = os.path.join("data", "processed", "val.csv")
    test_path = os.path.join("data", "processed", "test.csv")

    train_df.to_csv(train_path, index=False, encoding="utf-8")
    val_df.to_csv(val_path, index=False, encoding="utf-8")
    test_df.to_csv(test_path, index=False, encoding="utf-8")

    print(f"[+] Saved Train split: {train_path} ({len(train_df)} records - {len(train_df)/len(df):.1%})")
    print(f"[+] Saved Val split:   {val_path} ({len(val_df)} records - {len(val_df)/len(df):.1%})")
    print(f"[+] Saved Test split:  {test_path} ({len(test_df)} records - {len(test_df)/len(df):.1%})")
    print("[+] Zero-leakage guarantee verified across splits.")

    # Summary Statistics
    print("\n" + "=" * 70)
    print("Dataset Distribution Summary:")
    print("=" * 70)
    print("\nLanguages:")
    print(df["true_language"].value_counts(normalize=True).round(3))
    print("\nScripts:")
    print(df["script_type"].value_counts(normalize=True).round(3))
    print("\nPrimary Topics:")
    print(df["primary_topic"].value_counts())
    print("\nEmergent Drift Comments:")
    print(df["is_emergent_drift"].value_counts())
    print("\nTemporal Distribution:")
    print(df["academic_term"].value_counts())
    print("=" * 70)

if __name__ == "__main__":
    main()
