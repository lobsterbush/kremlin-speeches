"""
Geographic classification of White House speeches
Classifies by location (where) and participants (who) at continent/region level
"""

import pandas as pd
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GeographicClassifier:
    """Classify speeches by geographic location and participant origin"""
    
    def __init__(self):
        # Location keywords for regions/continents
        self.location_keywords = {
            'North America': [
                'Washington', 'White House', 'United States', 'USA', 'America', 'D.C.', 'DC',
                'New York', 'California', 'Texas', 'Florida', 'Chicago', 'Boston', 'Seattle',
                'Los Angeles', 'San Francisco', 'Atlanta', 'Philadelphia', 'Canada', 'Ottawa',
                'Toronto', 'Mexico', 'Mexico City'
            ],
            'Europe': [
                'Brussels', 'Paris', 'Berlin', 'London', 'Rome', 'Madrid', 'Warsaw', 'Prague',
                'Vienna', 'Budapest', 'Belgrade', 'Athens', 'Helsinki', 'Stockholm', 'Oslo',
                'Copenhagen', 'Amsterdam', 'Minsk', 'Kiev', 'Kyiv', 'Ukraine', 'Belarus',
                'Moldova', 'Bucharest', 'Sofia', 'Zagreb', 'Geneva', 'Zurich', 'Moscow', 'Russia'
            ],
            'Asia': [
                'Beijing', 'China', 'Tokyo', 'Japan', 'Seoul', 'South Korea', 'Delhi', 'India',
                'Mumbai', 'Singapore', 'Bangkok', 'Thailand', 'Vietnam', 'Hanoi', 'Manila',
                'Jakarta', 'Malaysia', 'Pyongyang', 'North Korea', 'DPRK', 'Mongolia',
                'Afghanistan', 'Kabul', 'Pakistan', 'Bangladesh', 'Myanmar', 'Taiwan', 'Taipei'
            ],
            'Middle East': [
                'Syria', 'Damascus', 'Iran', 'Tehran', 'Israel', 'Tel Aviv', 'Jerusalem',
                'Saudi Arabia', 'Riyadh', 'UAE', 'Dubai', 'Abu Dhabi', 'Qatar', 'Doha',
                'Kuwait', 'Bahrain', 'Oman', 'Yemen', 'Iraq', 'Baghdad', 'Jordan', 'Amman',
                'Lebanon', 'Beirut', 'Egypt', 'Cairo', 'Palestine'
            ],
            'Africa': [
                'South Africa', 'Johannesburg', 'Cape Town', 'Egypt', 'Cairo', 'Nigeria',
                'Ethiopia', 'Kenya', 'Nairobi', 'Morocco', 'Algeria', 'Tunisia', 'Libya',
                'Sudan', 'Zimbabwe', 'Angola', 'Mozambique'
            ],
            'South America': [
                'Brazil', 'Brasilia', 'Argentina', 'Buenos Aires', 'Chile', 'Santiago',
                'Peru', 'Lima', 'Colombia', 'Bogota', 'Venezuela', 'Caracas', 'Ecuador'
            ],
            'Central Asia': [
                'Kazakhstan', 'Astana', 'Uzbekistan', 'Tashkent', 'Kyrgyzstan', 'Bishkek',
                'Tajikistan', 'Dushanbe', 'Turkmenistan', 'Ashgabat'
            ],
            'Oceania': [
                'Australia', 'Sydney', 'Canberra', 'New Zealand', 'Wellington', 'Papua New Guinea'
            ]
        }
        
        # Country/organization to region mapping for participants
        self.participant_keywords = {
            'European': [
                'Germany', 'German', 'France', 'French', 'UK', 'British', 'Britain', 'Italy',
                'Italian', 'Spain', 'Spanish', 'Poland', 'Polish', 'EU', 'European Union',
                'Netherlands', 'Dutch', 'Belgium', 'Austrian', 'Austria', 'Switzerland',
                'Swiss', 'Sweden', 'Swedish', 'Norway', 'Norwegian', 'Denmark', 'Finnish',
                'Finland', 'Greece', 'Greek', 'Portugal', 'Czech', 'Hungary', 'Hungarian',
                'Romania', 'Bulgaria', 'Serbia', 'Croatia', 'Ukraine', 'Ukrainian', 'Belarus',
                'Belarusian', 'NATO'
            ],
            'Asian': [
                'China', 'Chinese', 'Japan', 'Japanese', 'Korea', 'Korean', 'India', 'Indian',
                'Vietnam', 'Vietnamese', 'Thailand', 'Singapore', 'Indonesia', 'Malaysian',
                'Philippines', 'Pakistan', 'Mongolian', 'Mongolia', 'Taiwan', 'Taiwanese',
                'Bangladesh', 'Myanmar', 'Burmese'
            ],
            'Middle Eastern': [
                'Syria', 'Syrian', 'Iran', 'Iranian', 'Israel', 'Israeli', 'Saudi', 'Turkey',
                'Turkish', 'UAE', 'Emirati', 'Qatar', 'Qatari', 'Kuwait', 'Kuwaiti', 'Iraq',
                'Iraqi', 'Jordan', 'Lebanese', 'Egypt', 'Egyptian', 'Palestinian', 'Yemeni',
                'Yemen'
            ],
            'African': [
                'South Africa', 'Nigerian', 'Ethiopia', 'Kenyan', 'Morocco', 'Moroccan',
                'Algeria', 'Algerian', 'Tunisia', 'Tunisian', 'Libya', 'Libyan', 'Sudan',
                'Zimbabwe', 'Angola', 'African'
            ],
            'North American': [
                'USA', 'American', 'United States', 'Canada', 'Canadian', 'Mexico', 'Mexican'
            ],
            'South American': [
                'Brazil', 'Brazilian', 'Argentina', 'Argentine', 'Chile', 'Chilean', 'Peru',
                'Peruvian', 'Colombia', 'Colombian', 'Venezuela', 'Venezuelan', 'Ecuador'
            ],
            'Central Asian': [
                'Kazakhstan', 'Kazakh', 'Uzbekistan', 'Uzbek', 'Kyrgyzstan', 'Kyrgyz',
                'Tajikistan', 'Tajik', 'Turkmenistan', 'Turkmen', 'Afghanistan', 'Afghan'
            ],
            'Oceanian': [
                'Australia', 'Australian', 'New Zealand', 'Papua New Guinea'
            ],
            'Russian': [
                'Russia', 'Russian', 'Moscow', 'Putin', 'Kremlin'
            ],
            'International': [
                'United Nations', 'UN', 'NATO', 'G7', 'G20', 'G8', 'WTO', 'IMF', 'World Bank'
            ]
        }
    
    def classify_location(self, location_text, title_text=""):
        """Classify geographic region based on location field"""
        if not location_text:
            location_text = ""
        
        combined_text = f"{location_text} {title_text}".lower()
        
        # Check each region
        regions_found = []
        for region, keywords in self.location_keywords.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    regions_found.append(region)
                    break
        
        # Return first match or 'US/Domestic' as default
        if regions_found:
            # If North America found and it's in US, classify as US/Domestic
            if 'North America' in regions_found:
                if any(k.lower() in combined_text for k in 
                    ['washington', 'white house', 'd.c.', 'dc', 'united states', 'usa', 'america']):
                    return 'US/Domestic'
            return regions_found[0]
        
        # Default to US/Domestic
        return 'US/Domestic'
    
    def classify_participants(self, title, category, content):
        """Classify participants' geographic origin"""
        # Handle NaN/missing values
        title = str(title) if title and title == title else ""
        category = str(category) if category and category == category else ""
        content = str(content) if content and content == content else ""
        
        combined_text = f"{title} {category} {content[:500]}".lower()  # Use first 500 chars of content
        
        regions_found = set()
        for region, keywords in self.participant_keywords.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    regions_found.add(region)
                    break
        
        # Default to American if no other participants found
        if not regions_found:
            return 'American'
        
        # If multiple regions, join them
        return '; '.join(sorted(regions_found))
    
    def classify_dataset(self, input_file, output_file):
        """Classify all speeches in dataset"""
        logger.info(f"Loading data from {input_file}")
        df = pd.read_csv(input_file)
        
        logger.info(f"Classifying {len(df)} speeches...")
        
        # Apply classifications
        df['location_region'] = df.apply(
            lambda row: self.classify_location(
                row.get('location', ''), 
                row.get('title', '')
            ), 
            axis=1
        )
        
        df['participant_region'] = df.apply(
            lambda row: self.classify_participants(
                row.get('title', ''),
                row.get('category', ''),
                row.get('content', '')
            ),
            axis=1
        )
        
        # Save classified dataset
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Saved classified data to {output_file}")
        
        # Print summary statistics
        print("\n=== Classification Summary ===")
        print("\nLocation Region Distribution:")
        print(df['location_region'].value_counts())
        print("\nParticipant Region Distribution:")
        print(df['participant_region'].value_counts())
        
        return df


if __name__ == "__main__":
    classifier = GeographicClassifier()
    
    # Classify the scraped data
    df = classifier.classify_dataset(
        input_file="whitehouse_speeches_lemmatized.csv",
        output_file="whitehouse_speeches_classified.csv"
    )
    
    print(f"\nClassification complete! Results saved to whitehouse_speeches_classified.csv")
